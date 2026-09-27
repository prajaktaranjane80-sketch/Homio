"""
CORE-004 T03 — Inventory Hierarchy & Relationships

Owns:
- project -> property relationship
- property -> unit relationship
- parent / child integrity
- relationship validation
- orphan prevention
- circular relationship prevention
- relationship versioning
- hierarchy reconstruction

Does NOT own:
- project identity
- inventory lifecycle
- availability transitions
- provenance
- commercial state
- concurrency policy
- authorization policy
- event transport
- REOS Control Center state
- ACRL execution

The hierarchy layer validates and reconstructs relationships between the
canonical Project / Inventory domain objects. It does not create another
inventory model or persistence store.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from .inventory import (
    Inventory,
    InventoryType,
)
from .project import Project


class InventoryHierarchyError(ValueError):
    """Base CORE-004 hierarchy error."""


class HierarchyValidationError(InventoryHierarchyError):
    """Raised when a hierarchy invariant is violated."""


class HierarchyTenantViolation(HierarchyValidationError):
    """Raised when hierarchy nodes cross tenant boundaries."""


class InventoryOrphanError(InventoryHierarchyError):
    """Raised when a required parent relationship is missing."""


class InventoryCircularRelationshipError(
    InventoryHierarchyError
):
    """Raised when a relationship graph contains a cycle."""


class RelationshipVersionError(
    InventoryHierarchyError
):
    """Raised when relationship versioning is invalid."""


class HierarchyNodeType(str, Enum):
    PROJECT = "PROJECT"
    PROPERTY = "PROPERTY"
    UNIT = "UNIT"


class RelationshipType(str, Enum):
    PROJECT_PROPERTY = "PROJECT_PROPERTY"
    PROPERTY_UNIT = "PROPERTY_UNIT"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise HierarchyValidationError(
            f"{name} must be a string."
        )

    value = value.strip()

    if not value:
        raise HierarchyValidationError(
            f"{name} cannot be empty."
        )

    return value


def _aware_time(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise HierarchyValidationError(
            f"{name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise HierarchyValidationError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


@dataclass(frozen=True, slots=True)
class HierarchyNodeRef:
    """Immutable reference to one hierarchy node."""

    node_type: HierarchyNodeType
    node_id: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.node_type,
            HierarchyNodeType,
        ):
            try:
                object.__setattr__(
                    self,
                    "node_type",
                    HierarchyNodeType(self.node_type),
                )
            except (TypeError, ValueError) as exc:
                raise HierarchyValidationError(
                    "node_type is invalid."
                ) from exc

        object.__setattr__(
            self,
            "node_id",
            _text(
                self.node_id,
                "node_id",
            ),
        )

    @property
    def key(self) -> tuple[str, str]:
        return (
            self.node_type.value,
            self.node_id,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "node_type": self.node_type.value,
            "node_id": self.node_id,
        }


@dataclass(frozen=True, slots=True)
class InventoryRelationship:
    """
    Immutable versioned hierarchy relationship.

    Allowed edges are deliberately narrow:

        PROJECT  -> PROPERTY
        PROPERTY -> UNIT
    """

    relationship_id: str
    tenant_id: str
    relationship_type: RelationshipType
    parent: HierarchyNodeRef
    child: HierarchyNodeRef
    relationship_version: int = 1
    created_at: datetime = _utc_now()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relationship_id",
            _text(
                self.relationship_id,
                "relationship_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        try:
            relationship_type = RelationshipType(
                self.relationship_type
            )
        except (TypeError, ValueError) as exc:
            raise HierarchyValidationError(
                "relationship_type is invalid."
            ) from exc

        object.__setattr__(
            self,
            "relationship_type",
            relationship_type,
        )

        if not isinstance(
            self.parent,
            HierarchyNodeRef,
        ):
            raise HierarchyValidationError(
                "parent must be HierarchyNodeRef."
            )

        if not isinstance(
            self.child,
            HierarchyNodeRef,
        ):
            raise HierarchyValidationError(
                "child must be HierarchyNodeRef."
            )

        if (
            isinstance(
                self.relationship_version,
                bool,
            )
            or not isinstance(
                self.relationship_version,
                int,
            )
            or self.relationship_version < 1
        ):
            raise RelationshipVersionError(
                "relationship_version must be >= 1."
            )

        object.__setattr__(
            self,
            "created_at",
            _aware_time(
                self.created_at,
                "created_at",
            ),
        )

        self._validate_edge()

    def _validate_edge(self) -> None:
        if self.parent.key == self.child.key:
            raise InventoryCircularRelationshipError(
                "A hierarchy node cannot be its own parent."
            )

        expected = {
            RelationshipType.PROJECT_PROPERTY: (
                HierarchyNodeType.PROJECT,
                HierarchyNodeType.PROPERTY,
            ),
            RelationshipType.PROPERTY_UNIT: (
                HierarchyNodeType.PROPERTY,
                HierarchyNodeType.UNIT,
            ),
        }[self.relationship_type]

        if self.parent.node_type is not expected[0]:
            raise HierarchyValidationError(
                "Relationship parent type is invalid: "
                f"expected={expected[0].value}, "
                f"actual={self.parent.node_type.value}"
            )

        if self.child.node_type is not expected[1]:
            raise HierarchyValidationError(
                "Relationship child type is invalid: "
                f"expected={expected[1].value}, "
                f"actual={self.child.node_type.value}"
            )

    @property
    def identity_key(self) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.parent.node_id,
            self.child.node_id,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "relationship_id": self.relationship_id,
            "tenant_id": self.tenant_id,
            "relationship_type": (
                self.relationship_type.value
            ),
            "parent": self.parent.to_dict(),
            "child": self.child.to_dict(),
            "relationship_version": self.relationship_version,
        }

        return hashlib.sha256(
            _canonical_json(payload).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "tenant_id": self.tenant_id,
            "relationship_type": (
                self.relationship_type.value
            ),
            "parent": self.parent.to_dict(),
            "child": self.child.to_dict(),
            "relationship_version": self.relationship_version,
            "created_at": self.created_at.isoformat(),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class InventoryHierarchy:
    """
    Immutable hierarchy snapshot.

    The object contains relationship truth for one tenant snapshot.
    It is not a persistence layer.

    Validation is graph-based even though CORE-004 currently allows only
    two edge types. This protects the model against malformed future
    relationship input.
    """

    tenant_id: str
    relationships: tuple[
        InventoryRelationship, ...
    ] = ()
    version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if (
            isinstance(self.version, bool)
            or not isinstance(self.version, int)
            or self.version < 1
        ):
            raise RelationshipVersionError(
                "hierarchy version must be >= 1."
            )

        normalized = tuple(
            self.relationships
        )

        for relationship in normalized:
            if not isinstance(
                relationship,
                InventoryRelationship,
            ):
                raise HierarchyValidationError(
                    "All relationships must be "
                    "InventoryRelationship."
                )

            if relationship.tenant_id != self.tenant_id:
                raise HierarchyTenantViolation(
                    "Relationship belongs to another tenant."
                )

        self._validate_unique_edges(
            normalized
        )
        self._validate_no_cycles(
            normalized
        )

        object.__setattr__(
            self,
            "relationships",
            normalized,
        )

    @staticmethod
    def _validate_unique_edges(
        relationships: Iterable[
            InventoryRelationship
        ],
    ) -> None:
        seen: set[tuple[str, str, str]] = set()

        for relationship in relationships:
            key = (
                relationship.relationship_type.value,
                relationship.parent.node_id,
                relationship.child.node_id,
            )

            if key in seen:
                raise HierarchyValidationError(
                    "Duplicate hierarchy relationship."
                )

            seen.add(key)

    @staticmethod
    def _validate_no_cycles(
        relationships: Iterable[
            InventoryRelationship
        ],
    ) -> None:
        adjacency: dict[
            tuple[str, str],
            set[tuple[str, str]],
        ] = {}

        for relationship in relationships:
            parent = relationship.parent.key
            child = relationship.child.key

            adjacency.setdefault(
                parent,
                set(),
            ).add(child)

            adjacency.setdefault(
                child,
                set(),
            )

        visiting: set[tuple[str, str]] = set()
        visited: set[tuple[str, str]] = set()

        def visit(
            node: tuple[str, str],
        ) -> None:
            if node in visiting:
                raise InventoryCircularRelationshipError(
                    "Circular inventory hierarchy detected."
                )

            if node in visited:
                return

            visiting.add(node)

            for child in adjacency.get(
                node,
                set(),
            ):
                visit(child)

            visiting.remove(node)
            visited.add(node)

        for node in tuple(adjacency):
            visit(node)

    def with_relationship(
        self,
        relationship: InventoryRelationship,
    ) -> "InventoryHierarchy":
        if relationship.tenant_id != self.tenant_id:
            raise HierarchyTenantViolation(
                "Cannot add relationship from another tenant."
            )

        for existing in self.relationships:
            if (
                existing.identity_key
                == relationship.identity_key
            ):
                raise HierarchyValidationError(
                    "Hierarchy relationship already exists."
                )

        return replace(
            self,
            relationships=(
                *self.relationships,
                relationship,
            ),
            version=self.version + 1,
        )

    def without_relationship(
        self,
        relationship_id: str,
    ) -> "InventoryHierarchy":
        relationship_id = _text(
            relationship_id,
            "relationship_id",
        )

        remaining = tuple(
            relationship
            for relationship in self.relationships
            if relationship.relationship_id
            != relationship_id
        )

        if len(remaining) == len(
            self.relationships
        ):
            raise HierarchyValidationError(
                "Hierarchy relationship does not exist."
            )

        return replace(
            self,
            relationships=remaining,
            version=self.version + 1,
        )

    def relationships_for_parent(
        self,
        parent: HierarchyNodeRef,
    ) -> tuple[
        InventoryRelationship, ...
    ]:
        return tuple(
            relationship
            for relationship in self.relationships
            if relationship.parent == parent
        )

    def relationships_for_child(
        self,
        child: HierarchyNodeRef,
    ) -> tuple[
        InventoryRelationship, ...
    ]:
        return tuple(
            relationship
            for relationship in self.relationships
            if relationship.child == child
        )

    def parent_of(
        self,
        child: HierarchyNodeRef,
    ) -> HierarchyNodeRef | None:
        matches = self.relationships_for_child(
            child
        )

        if not matches:
            return None

        if len(matches) > 1:
            raise HierarchyValidationError(
                "Child has multiple parents."
            )

        return matches[0].parent

    def validate_complete(
        self,
        *,
        project_ids: Iterable[str],
        inventories: Iterable[Inventory],
    ) -> None:
        """
        Validate the complete project/property/unit hierarchy.

        Every PROPERTY must have exactly one project parent.
        Every UNIT must have exactly one property parent.
        """
        projects = {
            _text(
                project_id,
                "project_id",
            )
            for project_id in project_ids
        }

        inventory_map = {
            inventory.inventory_id: inventory
            for inventory in inventories
        }

        for inventory in inventory_map.values():
            if inventory.tenant_id != self.tenant_id:
                raise HierarchyTenantViolation(
                    "Inventory belongs to another tenant."
                )

            if inventory.inventory_type is (
                InventoryType.DEVELOPMENT
            ):
                continue

            if inventory.inventory_type is (
                InventoryType.PROPERTY
            ):
                child = HierarchyNodeRef(
                    HierarchyNodeType.PROPERTY,
                    inventory.inventory_id,
                )

                parents = self.relationships_for_child(
                    child
                )

                if len(parents) != 1:
                    raise InventoryOrphanError(
                        "PROPERTY inventory must have "
                        "exactly one project parent."
                    )

                parent = parents[0].parent

                if (
                    parent.node_id
                    not in projects
                ):
                    raise InventoryOrphanError(
                        "PROPERTY references a "
                        "non-existent project."
                    )

            elif inventory.inventory_type is (
                InventoryType.UNIT
            ):
                child = HierarchyNodeRef(
                    HierarchyNodeType.UNIT,
                    inventory.inventory_id,
                )

                parents = self.relationships_for_child(
                    child
                )

                if len(parents) != 1:
                    raise InventoryOrphanError(
                        "UNIT inventory must have "
                        "exactly one property parent."
                    )

                parent = parents[0].parent

                parent_inventory = inventory_map.get(
                    parent.node_id
                )

                if parent_inventory is None:
                    raise InventoryOrphanError(
                        "UNIT references a "
                        "non-existent property."
                    )

                if parent_inventory.inventory_type is not (
                    InventoryType.PROPERTY
                ):
                    raise HierarchyValidationError(
                        "UNIT parent must be PROPERTY."
                    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "version": self.version,
            "relationships": [
                relationship.to_dict()
                for relationship in self.relationships
            ],
        }


def project_property_relationship(
    *,
    relationship_id: str,
    tenant_id: str,
    project_id: str,
    property_id: str,
    relationship_version: int = 1,
    at: datetime | None = None,
) -> InventoryRelationship:
    """
    Create the only allowed PROJECT -> PROPERTY edge.
    """
    return InventoryRelationship(
        relationship_id=relationship_id,
        tenant_id=tenant_id,
        relationship_type=(
            RelationshipType.PROJECT_PROPERTY
        ),
        parent=HierarchyNodeRef(
            HierarchyNodeType.PROJECT,
            project_id,
        ),
        child=HierarchyNodeRef(
            HierarchyNodeType.PROPERTY,
            property_id,
        ),
        relationship_version=relationship_version,
        created_at=(
            _utc_now()
            if at is None
            else at
        ),
    )


def property_unit_relationship(
    *,
    relationship_id: str,
    tenant_id: str,
    property_id: str,
    unit_id: str,
    relationship_version: int = 1,
    at: datetime | None = None,
) -> InventoryRelationship:
    """
    Create the only allowed PROPERTY -> UNIT edge.
    """
    return InventoryRelationship(
        relationship_id=relationship_id,
        tenant_id=tenant_id,
        relationship_type=(
            RelationshipType.PROPERTY_UNIT
        ),
        parent=HierarchyNodeRef(
            HierarchyNodeType.PROPERTY,
            property_id,
        ),
        child=HierarchyNodeRef(
            HierarchyNodeType.UNIT,
            unit_id,
        ),
        relationship_version=relationship_version,
        created_at=(
            _utc_now()
            if at is None
            else at
        ),
    )


def reconstruct_hierarchy(
    *,
    tenant_id: str,
    projects: Iterable[Project],
    inventories: Iterable[Inventory],
    relationships: Iterable[InventoryRelationship],
) -> InventoryHierarchy:
    """
    Reconstruct a hierarchy snapshot from canonical domain objects and
    relationship records.

    No persistence access and no autonomous discovery are performed.
    """
    tenant_id = _text(
        tenant_id,
        "tenant_id",
    )

    projects = tuple(projects)
    inventories = tuple(inventories)
    relationships = tuple(relationships)

    for project in projects:
        if project.tenant_id != tenant_id:
            raise HierarchyTenantViolation(
                "Project belongs to another tenant."
            )

    for inventory in inventories:
        if inventory.tenant_id != tenant_id:
            raise HierarchyTenantViolation(
                "Inventory belongs to another tenant."
            )

    hierarchy = InventoryHierarchy(
        tenant_id=tenant_id,
        relationships=relationships,
        version=1,
    )

    hierarchy.validate_complete(
        project_ids=(
            project.project_id
            for project in projects
        ),
        inventories=inventories,
    )

    return hierarchy


__all__ = [
    "HierarchyNodeRef",
    "HierarchyNodeType",
    "InventoryCircularRelationshipError",
    "InventoryHierarchy",
    "InventoryHierarchyError",
    "InventoryOrphanError",
    "InventoryRelationship",
    "HierarchyTenantViolation",
    "HierarchyValidationError",
    "RelationshipType",
    "RelationshipVersionError",
    "project_property_relationship",
    "property_unit_relationship",
    "reconstruct_hierarchy",
]
