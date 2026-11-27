# Regression gate

`make test-regression` runs `scripts/regression_gate.py`. It recomputes the SDK's public surface and guaranteed
behaviour and compares it byte for byte with the golden files in `golden/`.

- A difference fails the gate. Decide first whether the change is intended: a breaking change needs a MAJOR version
  after 1.0, migration notes, a changelog entry and an approved decision. Then run `make regression-golden WRITE=1`
  and review the golden diff in the same pull request.
- `make regression-golden` without `WRITE=1` shows whether the golden data are current and changes nothing.
- A fixed defect adds a case here (and a row in `REGRESSION_INVENTORY.md`).
- The vendored fixtures and contract files are pinned separately (`make schema-drift`).
