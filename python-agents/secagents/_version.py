"""Centralized version management for SecAgents."""

__version__ = "0.2.0"
__release_date__ = "2026-05-20"
__author__ = "SecAgents Contributors"
__license__ = "MIT"

# Semantic versioning breakdown
VERSION_MAJOR = 0
VERSION_MINOR = 2
VERSION_PATCH = 0
VERSION_PRERELEASE = None  # None for stable, "alpha"/"beta"/"rc" otherwise

def get_version_string() -> str:
    """Get full version string."""
    version = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
    if VERSION_PRERELEASE:
        version += f"-{VERSION_PRERELEASE}"
    return version

def get_version_tuple() -> tuple:
    """Get version as tuple for comparison."""
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
