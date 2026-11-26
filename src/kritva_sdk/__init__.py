"""kritva_sdk: contract-first Python SDK for Kritva (preview).

The base import has no dependency outside the standard library and does not import ROS 2, a simulator, hardware
or a network library. Configuration, typed errors and contract compatibility declarations are available now; the
vendored Sense schema and the typed Sense models are added by later KOS-SDK-003 stages.
"""
from kritva_sdk._version import __version__
from kritva_sdk.compat import supported_contracts
from kritva_sdk.config import SdkConfig

__all__ = ["SdkConfig", "__version__", "supported_contracts"]
