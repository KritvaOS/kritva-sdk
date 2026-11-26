"""Explicit, immutable SDK configuration.

There is no global mutable configuration and no implicit loading from the environment or files. A configuration
is constructed explicitly by the caller and validated on construction. It carries no credentials, endpoints,
timeouts or retry policy: this SDK release has no transport (see ARCHITECTURE.md).
"""
from __future__ import annotations

from dataclasses import dataclass

from kritva_sdk.compat import require_supported

__all__ = ["SdkConfig"]


@dataclass(frozen=True, slots=True)
class SdkConfig:
    """Immutable SDK configuration.

    Attributes:
        sense_contract_version: Sense contract version the caller expects. Must be supported by this release;
            otherwise construction raises ``UnsupportedContractVersion`` (or ``ContractError`` for a non-string).
    """

    sense_contract_version: str = "0.1.0"

    def __post_init__(self) -> None:
        require_supported("sense", self.sense_contract_version, path="sense_contract_version")
