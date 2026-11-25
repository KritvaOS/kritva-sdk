"""kritva_sdk: contract-first Python SDK for Kritva (preview).

The base import has no dependency outside the standard library and does not import ROS 2, a simulator, hardware
or a network library. No contract models or validators exist yet; they are added by KOS-SDK-003 over vendored,
pinned schemas.
"""
from kritva_sdk._version import __version__

__all__ = ["__version__"]
