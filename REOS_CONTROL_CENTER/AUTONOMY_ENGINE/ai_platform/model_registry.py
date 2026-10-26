"""Deterministic, allowlisted provider and model registries.

These registries select configured routes and provider adapters only.
They do not authenticate users, authorize business operations, or enable
live providers by themselves.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .contracts import ModelRoute, _identifier
from .errors import ModelResolutionError
from .ports import ProviderPort

_MODEL_CAPABILITIES = frozenset(
    {
        "text_generation",
        "embeddings",
    }
)


@dataclass(frozen=True, slots=True)
class ModelDefinition:
    """Immutable, auditable metadata for one explicitly configured model."""

    route: ModelRoute
    provider_version: str
    model_version: str
    capabilities: tuple[str, ...] = ("text_generation",)
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.route, ModelRoute):
            raise TypeError("route must be a ModelRoute")

        object.__setattr__(
            self,
            "provider_version",
            _identifier(self.provider_version, "provider_version"),
        )
        object.__setattr__(
            self,
            "model_version",
            _identifier(self.model_version, "model_version"),
        )

        if isinstance(self.capabilities, (str, bytes)):
            raise TypeError("capabilities must be a sequence of identifiers")

        try:
            capabilities = tuple(
                _identifier(value, "capability")
                for value in self.capabilities
            )
        except TypeError as exc:
            raise TypeError(
                "capabilities must be an iterable of identifiers"
            ) from exc

        if not capabilities:
            raise ValueError("at least one model capability is required")

        if len(set(capabilities)) != len(capabilities):
            raise ValueError("duplicate model capabilities are not allowed")

        if not set(capabilities).issubset(_MODEL_CAPABILITIES):
            raise ValueError("unsupported model capability")

        object.__setattr__(self, "capabilities", capabilities)

        if isinstance(self.aliases, (str, bytes)):
            raise TypeError("aliases must be a sequence of identifiers")

        try:
            aliases = tuple(
                _identifier(value, "model_alias")
                for value in self.aliases
            )
        except TypeError as exc:
            raise TypeError(
                "aliases must be an iterable of identifiers"
            ) from exc

        if len(set(aliases)) != len(aliases):
            raise ValueError("duplicate model aliases are not allowed")

        object.__setattr__(self, "aliases", aliases)


class ModelRegistry:
    """Resolve only configured models, aliases and supported capabilities."""

    __slots__ = ("_lookup", "_allowed_provider_ids", "_model_ids")

    def __init__(
        self,
        definitions: Iterable[ModelDefinition],
        *,
        allowed_provider_ids: Iterable[str],
    ) -> None:
        if isinstance(definitions, (str, bytes)):
            raise TypeError("definitions must be model definitions")

        try:
            configured_definitions = tuple(definitions)
        except TypeError as exc:
            raise TypeError(
                "definitions must be an iterable of ModelDefinition"
            ) from exc

        if not configured_definitions:
            raise ValueError("at least one model definition is required")

        if isinstance(allowed_provider_ids, (str, bytes)):
            raise TypeError(
                "allowed_provider_ids must be a sequence of identifiers"
            )

        try:
            provider_ids = tuple(
                _identifier(value, "allowed_provider_id")
                for value in allowed_provider_ids
            )
        except TypeError as exc:
            raise TypeError(
                "allowed_provider_ids must be iterable"
            ) from exc

        if not provider_ids:
            raise ValueError(
                "at least one provider identifier must be explicitly allowed"
            )

        if len(set(provider_ids)) != len(provider_ids):
            raise ValueError(
                "duplicate provider identifiers are not allowed"
            )

        allowed_providers = frozenset(provider_ids)
        lookup: dict[str, ModelDefinition] = {}
        model_ids: list[str] = []

        for definition in configured_definitions:
            if not isinstance(definition, ModelDefinition):
                raise TypeError(
                    "every model registry entry must be a ModelDefinition"
                )

            route = definition.route

            if route.provider_id not in allowed_providers:
                raise ValueError(
                    "a model route references a provider outside "
                    "the configured provider allowlist"
                )

            if route.model_id in model_ids:
                raise ValueError("duplicate canonical model identifier")

            model_ids.append(route.model_id)

            for identifier in (route.model_id, *definition.aliases):
                if identifier in lookup:
                    raise ValueError(
                        "model identifiers and aliases must be globally unique"
                    )
                lookup[identifier] = definition

        self._lookup = MappingProxyType(lookup)
        self._allowed_provider_ids = tuple(sorted(allowed_providers))
        self._model_ids = tuple(sorted(model_ids))

    @property
    def allowed_provider_ids(self) -> tuple[str, ...]:
        """Return the configured provider allowlist, without credentials."""
        return self._allowed_provider_ids

    @property
    def model_ids(self) -> tuple[str, ...]:
        """Return canonical model identifiers, not aliases."""
        return self._model_ids

    def resolve_definition(
        self,
        model_id: str,
        *,
        required_capability: str = "text_generation",
    ) -> ModelDefinition:
        """Resolve canonical IDs or aliases with explicit capability checks.

        This method returns version metadata for audit and future integration.
        A successful resolution is not an authorization decision.
        """
        if required_capability not in _MODEL_CAPABILITIES:
            raise ValueError("unsupported required model capability")

        try:
            requested_id = _identifier(model_id, "model_id")
        except (TypeError, ValueError):
            raise ModelResolutionError() from None

        definition = self._lookup.get(requested_id)

        if definition is None:
            raise ModelResolutionError()

        if not definition.route.enabled:
            raise ModelResolutionError()

        if required_capability not in definition.capabilities:
            raise ModelResolutionError()

        return definition

    def resolve(self, model_id: str) -> ModelRoute:
        """Resolve an enabled text-generation route for the existing gateway."""
        return self.resolve_definition(
            model_id,
            required_capability="text_generation",
        ).route


class ProviderRegistry:
    """Immutable allowlist of already-constructed provider adapters.

    No SDK, credentials, environment variables or network clients are created
    by this class. Adapters are injected by their approved runtime owner.
    """

    __slots__ = ("_providers",)

    def __init__(
        self,
        providers: Mapping[str, ProviderPort],
    ) -> None:
        if not isinstance(providers, Mapping):
            raise TypeError("providers must be a provider-ID mapping")

        normalized: dict[str, ProviderPort] = {}

        for raw_provider_id, provider in providers.items():
            provider_id = _identifier(
                raw_provider_id,
                "provider_id",
            )

            if provider_id in normalized:
                raise ValueError(
                    "duplicate normalized provider identifiers are not allowed"
                )

            if not callable(getattr(provider, "generate", None)):
                raise TypeError(
                    "each provider adapter must expose a callable generate method"
                )

            normalized[provider_id] = provider

        self._providers = MappingProxyType(normalized)

    @property
    def provider_ids(self) -> tuple[str, ...]:
        """Return configured provider identifiers, never adapter details."""
        return tuple(sorted(self._providers))

    def get(self, provider_id: str) -> ProviderPort | None:
        """Return a registered adapter or None when it is unavailable."""
        try:
            requested_id = _identifier(provider_id, "provider_id")
        except (TypeError, ValueError):
            return None

        return self._providers.get(requested_id)
