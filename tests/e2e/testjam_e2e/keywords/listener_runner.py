import os
import subprocess

from robot.api import logger
from robot.api.deco import keyword


LISTENER_TIMEOUT_SECONDS = 120


class ListenerRunnerMixin:
    """Keywords that drive the testjam-listener Robot Framework integration."""

    @keyword("I configure the listener to target project ${name}")
    def configure_listener_project(self, name: str) -> None:
        self.listener_project_name = name

    @keyword("I run the listener against fixture ${path}")
    def run_listener(self, path: str) -> None:
        assert getattr(self, "listener_project_name", None), (
            "Set the listener project first with 'I configure the listener to target project ...'"
        )
        env = self._listener_environment()
        completed = subprocess.run(
            [
                "robot",
                "--listener", "testjam_listener.TestjamListener",
                "--outputdir", "/tmp/listener_run",
                path,
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=LISTENER_TIMEOUT_SECONDS,
        )
        logger.info(f"Listener stdout:\n{completed.stdout}")
        if completed.returncode not in (0, 1):
            raise AssertionError(
                f"Listener subprocess returned {completed.returncode}:\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}",
            )
        self._select_listener_project()

    @keyword("the listener project should have ${count} executions")
    def listener_project_should_have_executions(self, count: str) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/executions",
        )
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} executions, got {actual}"

    @keyword("the latest listener execution should have ${count} results")
    def latest_execution_should_have_results(self, count: str) -> None:
        self._select_latest_execution()
        response = self.client.get(f"/executions/{self.current_execution_id}/results")
        actual = len(response.json())
        assert actual == int(count), f"Expected {count} results, got {actual}"

    @keyword("the latest listener execution should be completed")
    def latest_execution_should_be_completed(self) -> None:
        self._select_latest_execution()
        response = self.client.get(f"/executions/{self.current_execution_id}")
        actual = response.json()["status"]
        assert actual == "completed", f"Expected 'completed', got '{actual}'"

    @keyword("the latest listener execution should have a ${status} result for case ${name}")
    def latest_execution_should_have_status_for_case(self, status: str, name: str) -> None:
        self._select_latest_execution()
        results = self.client.get(
            f"/executions/{self.current_execution_id}/results",
        ).json()
        for result in results:
            if result.get("test_case_title") == name:
                assert result["status"] == status, (
                    f"Expected '{status}' for '{name}', got '{result['status']}'"
                )
                return
        raise AssertionError(f"No result for case '{name}'")

    @keyword("the latest listener execution should have at least one step result")
    def latest_execution_should_have_step_results(self) -> None:
        self._select_latest_execution()
        results = self.client.get(
            f"/executions/{self.current_execution_id}/results",
        ).json()
        for result in results:
            if result.get("step_results"):
                return
        raise AssertionError("No step results found on the latest execution")

    @keyword("the latest listener execution should have step result logs containing ${text}")
    def latest_execution_step_logs_should_contain(self, text: str) -> None:
        self._select_latest_execution()
        results = self.client.get(
            f"/executions/{self.current_execution_id}/results",
        ).json()
        for result in results:
            for step_result in result.get("step_results", []):
                if text in (step_result.get("log_output") or ""):
                    return
        raise AssertionError(f"No step result log contains '{text}'")

    def _listener_environment(self) -> dict:
        env = dict(os.environ)
        env.update({
            "TESTJAM_API_URL": self.base_url,
            "TESTJAM_USER": os.getenv("TESTJAM_USER", "admin"),
            "TESTJAM_PASS": os.getenv("TESTJAM_PASS", "admin123"),
            "TESTJAM_PROJECT": self.listener_project_name,
        })
        return env

    def _select_listener_project(self) -> None:
        for project in self.client.get("/projects").json():
            if project["name"] == self.listener_project_name:
                self.current_project_id = project["id"]
                return
        raise AssertionError(
            f"Listener project '{self.listener_project_name}' was not created by the run",
        )

    def _select_latest_execution(self) -> None:
        executions = self.client.get(
            f"/projects/{self.current_project_id}/executions",
        ).json()
        assert executions, "Project has no executions"
        latest = max(executions, key=lambda execution: execution["id"])
        self.current_execution_id = latest["id"]
