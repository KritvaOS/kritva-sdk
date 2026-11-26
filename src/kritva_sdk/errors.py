"""Typed errors for kritva_sdk.

Contract errors preserve the upstream violation codes (for the Sense contract these are the codes defined by
contract/SENSE_CONTRACT.md) unchanged, together with the field path and message. Error text never contains
credentials or other secrets: it describes the offending field and the rule, not configuration values beyond the
rejected contract version string.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SdkError", "Violation", "ContractError", "UnsupportedContractVersion"]

# Upstream code used when a contract version is not supported by this SDK release.
UNSUPPORTED_CONTRACT_VERSION = "UNSUPPORTED_CONTRACT_VERSION"
MALFORMED_FIELD = "MALFORMED_FIELD"


class SdkError(Exception):
    """Base class for every error raised deliberately by kritva_sdk."""


@dataclass(frozen=True, order=True)
class Violation:
    """One contract violation, shaped like the upstream (code, path, message) tuple.

    Ordering is by (path, code, message), matching the upstream deterministic ordering.
    """

    path: str
    code: str
    message: str

    def as_tuple(self) -> tuple[str, str, str]:
        """Return the upstream-shaped (code, path, message) tuple."""
        return (self.code, self.path, self.message)


class ContractError(SdkError):
    """A value does not satisfy a pinned contract.

    ``code``, ``path`` and ``message`` describe the first violation (in deterministic (path, code, message)
    order); ``violations`` holds all of them.
    """

    def __init__(self, violations: tuple[Violation, ...] | list[Violation]) -> None:
        vs = tuple(sorted(violations))
        if not vs:
            raise ValueError("ContractError requires at least one violation")
        self.violations: tuple[Violation, ...] = vs
        first = vs[0]
        self.code: str = first.code
        self.path: str = first.path
        self.message: str = first.message
        super().__init__(f"{first.code} at {first.path or '<root>'}: {first.message}")

    @classmethod
    def single(cls, code: str, path: str, message: str) -> "ContractError":
        return cls([Violation(path=path, code=code, message=message)])


class UnsupportedContractVersion(ContractError):
    """The requested or supplied contract version is not supported by this SDK release."""

    @classmethod
    def for_version(cls, contract: str, version: str, path: str, supported: tuple[str, ...]) -> "UnsupportedContractVersion":
        msg = f"{contract} contract version {version!r} is not supported; supported: {', '.join(supported)}"
        return cls([Violation(path=path, code=UNSUPPORTED_CONTRACT_VERSION, message=msg)])
