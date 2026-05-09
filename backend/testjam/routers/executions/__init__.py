"""Test executions router package.

Split from a single 1.2k-line module. Routers are defined here and shared with
submodules; importing the submodules at the bottom triggers their endpoint
decorators against these router instances.
"""
import os

from fastapi import APIRouter

from testjam.core.config import settings

# Per-resource upload subdirs used by attachment endpoints.
UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "results")
EXECUTION_UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "executions")

projects_router = APIRouter(prefix="/projects", tags=["TestExecutions"])
executions_router = APIRouter(prefix="/executions", tags=["TestExecutions"])
results_router = APIRouter(prefix="/results", tags=["TestResults"])

# Submodule imports register endpoints on the routers above.
from testjam.routers.executions import crud, exports, attachments, results, result_imports  # noqa: E402, F401
