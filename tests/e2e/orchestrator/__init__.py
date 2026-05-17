"""Testjam e2e orchestrator.

Discovers every ``.robot`` suite file under a root directory, launches one
``robot`` subprocess per suite, and reports a summary at the end. Each
subprocess runs against the same project + version (via env vars) so the
listener attaches every per-suite execution to the same git commit.

This sidesteps the live-scroll degradation that happens when many tests share
a single execution: each Robot subprocess produces its own Testjam execution
with serial step events, and the orchestrator parallelises across executions
rather than across tests inside one.
"""
