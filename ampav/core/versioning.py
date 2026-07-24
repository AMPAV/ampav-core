"""Installed package version helpers."""

from importlib.metadata import PackageNotFoundError, version


def package_version(
    distribution_name: str,
    *,
    fallback: str = "0+unknown",
) -> str:
    """Return an installed distribution's version or a fallback if not found."""
    try:
        return version(distribution_name)
    except PackageNotFoundError:
        return fallback
