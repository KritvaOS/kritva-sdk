# Regression inventory

Cases run by `make test-regression` (`scripts/regression_gate.py`). Each compares the SDK's observable behaviour with
golden data in `tests/regression/golden/`. A failing, missing or empty case fails the gate.

| Case | Guarantee | Golden data |
|---|---|---|
| REG-01 | Public API: `__all__`, classes, bases, public methods and signatures of every public module | `public_api.json` |
| REG-02 | `supported_contracts()` | `supported_contracts.json` |
| REG-03 | Sense contract constants: version, error codes, frames, clocks, timestamp unit, validity states, kinds and units | `contract_constants.json` |
| REG-04 | `validate_sample` result (code, path, message) for every vendored upstream fixture | `fixture_violations.json` |
| REG-05 | Error behaviour: violation ordering, first-violation code and path, text, and early failure on an unsupported contract version | `error_behaviour.json` |
| REG-06 | `SdkConfig` fields, defaults, immutability and rejection | `config.json` |
| REG-07 | Package version and the vendored contract file hashes, tag and commit | `vendored_and_version.json` |

Changing a golden file changes a public interface or a guaranteed behaviour. After 1.0 that needs a MAJOR version, a
changelog entry and an approved decision. See `tests/regression/README.md`.
