"""Unit-level coverage for the upload sanitization helpers.

`uploads.safe_filename` must never return a string that contains a path
separator or escapes a single directory level. `uploads.safe_join` must
always resolve inside the requested root, even when callers forget to
sanitize first.
"""
import os

import pytest

from testjam.services import uploads
from tests.security.payloads import PATH_TRAVERSAL_FILENAMES


@pytest.mark.parametrize("payload", PATH_TRAVERSAL_FILENAMES)
def test_safe_filename_strips_separators_and_traversal(payload):
    cleaned = uploads.safe_filename(payload)

    assert "/" not in cleaned
    assert "\\" not in cleaned
    assert cleaned not in ("", ".", "..")


@pytest.mark.parametrize("payload", PATH_TRAVERSAL_FILENAMES)
def test_safe_join_stays_within_root(tmp_path, payload):
    root = str(tmp_path)

    resolved = uploads.safe_join(root, payload)

    real_root = os.path.realpath(root)
    assert os.path.realpath(resolved).startswith(real_root + os.sep)
