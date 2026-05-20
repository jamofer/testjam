from robot.api.deco import keyword


class CustomFieldsMixin:
    """Keywords covering project custom field definitions and values."""

    @keyword("I create a priority custom field for bugs")
    def create_priority_field_for_bugs(self) -> int:
        payload = {
            "entity_type": "bug",
            "key": "priority",
            "label": "Priority",
            "type": "single_select",
            "options": [
                {"value": "p0", "label": "P0", "color": "#ef4444"},
                {"value": "p1", "label": "P1"},
            ],
        }
        response = self.client.post(
            f"/projects/{self.current_project_id}/custom-fields", json=payload,
        )
        assert response.status_code == 201, response.text
        self.current_custom_field_id = response.json()["id"]
        return self.current_custom_field_id

    @keyword("I create a bug titled ${title} with priority ${value}")
    def create_bug_with_priority(self, title: str, value: str) -> int:
        response = self.client.post(
            f"/projects/{self.current_project_id}/bugs",
            json={"title": title, "custom_fields": {"priority": value}},
        )
        assert response.status_code == 201, response.text
        self.current_bug_id = response.json()["id"]
        return self.current_bug_id

    @keyword("the bug list filtered by priority ${value} should have ${count} entries")
    def filtered_bug_list_should_have(self, value: str, count: str) -> None:
        response = self.client.get(
            f"/projects/{self.current_project_id}/bugs",
            params={"cf_key": "priority", "cf_value": value},
        )
        assert response.status_code == 200, response.text
        actual = len(response.json())
        expected = int(count)
        assert actual == expected, f"Expected {expected} bugs, got {actual}"
