"""GET /about — build metadata for the running instance.

Powers the in-app About dialog and version chip. Read-only, unauthenticated:
the same metadata is already exposed through `/health` and there's no secret
material in here (just the package version, git ref, short commit and build
timestamp injected at image build time).
"""
import os
from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter

UNKNOWN = "unknown"

router = APIRouter(tags=["About"])


@router.get("/about")
def about() -> dict:
    return {
        "version": _package_version(),
        "ref": os.getenv("TESTJAM_VERSION_REF") or UNKNOWN,
        "commit": os.getenv("TESTJAM_VERSION_COMMIT") or UNKNOWN,
        "built_at": os.getenv("TESTJAM_BUILD_DATE") or UNKNOWN,
    }


def _package_version() -> str:
    try:
        return version("testjam-api")
    except PackageNotFoundError:
        return UNKNOWN
