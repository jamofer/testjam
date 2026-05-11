from robot.api.deco import keyword


class CaseStepReorderMixin:
    """Keywords covering step reordering inside a test case."""

    @keyword("I reorder the steps to ${actions}")
    def reorder_steps(self, actions: str) -> None:
        expected_order = [name.strip() for name in actions.split(",") if name.strip()]
        steps = self.client.get(f"/cases/{self.current_case_id}/steps").json()
        by_action = {step["action"]: step["id"] for step in steps}
        ordered_ids = [by_action[name] for name in expected_order]
        response = self.client.post(
            f"/cases/{self.current_case_id}/steps/reorder",
            json={"step_ids": ordered_ids},
        )
        assert response.status_code == 200, response.text

    @keyword("the test case steps should be ordered as ${actions}")
    def case_steps_should_be_ordered_as(self, actions: str) -> None:
        expected = [name.strip() for name in actions.split(",") if name.strip()]
        steps = self.client.get(f"/cases/{self.current_case_id}/steps").json()
        actual = [step["action"] for step in steps]
        assert actual == expected, f"Expected order {expected}, got {actual}"
