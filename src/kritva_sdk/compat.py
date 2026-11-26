"""Contract compatibility declarations.

The SDK declares exactly which contract versions it implements. Unsupported versions fail early, before any
semantic validation is attempted under a version this release does not implement.
"""
from __future__ import annotations

from kritva_sdk.errors import MALFORMED_FIELD, ContractError, UnsupportedContractVersion

__all__ = ["supported_contracts", "require_supported"]

_SUPPORTED: dict[str, tuple[str, ...]] = {"sense": ("0.1.0",)}


def supported_contracts() -> dict[str, tuple[str, ...]]:
    """Return a fresh mapping of contract name to supported versions, e.g. ``{"sense": ("0.1.0",)}``."""
    return dict(_SUPPORTED)


def require_supported(contract: str, version: object, path: str = "contract_version") -> str:
    """Return ``version`` if this SDK supports it for ``contract``, otherwise raise.

    A non-string version raises ``ContractError`` with code MALFORMED_FIELD; an unsupported string raises
    ``UnsupportedContractVersion`` with code UNSUPPORTED_CONTRACT_VERSION. An unknown contract name is a
    programming error and raises ``ValueError``.
    """
    if contract not in _SUPPORTED:
        raise ValueError(f"unknown contract {contract!r}")
    if not isinstance(version, str):
        raise ContractError.single(MALFORMED_FIELD, path, "contract version must be a string")
    supported = _SUPPORTED[contract]
    if version not in supported:
        raise UnsupportedContractVersion.for_version(contract, version, path, supported)
    return version
