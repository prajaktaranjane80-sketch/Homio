# T17 Implementation

This package hardens T17 without changing T16/T13/T14.

T17 consumes T16 repository intelligence and its static dependency graph. It adds:
- reverse dependency traversal
- transitive blast radius
- protected/unknown classification
- deterministic immutable report
- read-only/security policy
- provenance/version contract
- metrics and integration handoff
- adversarial and integration tests

Before Git update, run the T17 suite and then the full ACRL regression on the local Windows repository.
