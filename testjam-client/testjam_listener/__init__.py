"""Compatibility shim — preserves the historical ``testjam_listener`` import path.

Robot Framework configurations that pre-date the monorepo merge can keep using
``--listener testjam_listener.TestjamListener``; new code should import from
``testjam_client.listener`` directly.
"""
from testjam_client.listener import TestjamListener
from testjam_client.listener import git_version, listener, log, status

__all__ = ["TestjamListener", "git_version", "listener", "log", "status"]
