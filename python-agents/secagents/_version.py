"""Centralized version management for SecAgents."""

__version__ = "0.3.0-dev"
__release_date__ = "2026-06-01"
__author__ = "SecAgents Contributors"
__license__ = "MIT"

# Semantic versioning breakdown
VERSION_MAJOR = 0
VERSION_MINOR = 3
VERSION_PATCH = 0
VERSION_PRERELEASE = "dev"  # None for stable, "alpha"/"beta"/"rc" otherwise


def get_version_string() -> str:
    """Get full version string."""
    version = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
    if VERSION_PRERELEASE:
        version += f"-{VERSION_PRERELEASE}"
    return version


def get_version_tuple() -> tuple:
    """Get version as tuple for comparison."""
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
