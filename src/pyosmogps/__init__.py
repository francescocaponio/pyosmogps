from typing import NamedTuple

from .pyosmogps import OsmoGps  # noqa: F401

__package_name__ = "pyosmogps"


class _VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

    @property
    def version_str(self) -> str:
        release_level = f".{self.releaselevel}" if self.releaselevel else ""
        return f"{self.major}.{self.minor}.{self.micro}{release_level}"


# Leave version as a placeholder,
# it will be updated by check_package_version.py
# during the build process.
__version_info__ = _VersionInfo(
    major=0,
    minor=0,
    micro=1,
    releaselevel="dev0",
    serial=0,
)

__version__ = __version_info__.version_str
VERSION = __version__  # synonym for backwards compatibility
