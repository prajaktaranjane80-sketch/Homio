# F01 — Experience Foundation

## Module boundary rule

The permanent frontend coding rule is:

> One named production module = one source file.

A file may contain related TypeScript types, constants and helpers required internally by that module, but unrelated production modules must not be merged into the same file.

Allowed exceptions:

- configuration files
- route/page entry files
- `index.ts` barrel files when later introduced
- test files
- generated files

The F01 layer owns:

- production shell
- responsive shell
- shared visual primitives
- loading/error/empty foundation
- navigation presentation foundation
- accessibility-safe interaction foundation

The F01 layer does not own:

- inventory truth
- search truth
- lead truth
- ownership truth
- deal truth
- financial truth
- trust/fraud/governance truth
- identity or tenant authority
- ACRL runtime behavior
- Control Center state

Feature layers F02–F13 must consume F01 rather than rebuild equivalent modules.
