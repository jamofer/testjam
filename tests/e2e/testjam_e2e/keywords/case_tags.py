from robot.api.deco import keyword


class CaseTagsMixin:
    """Keywords covering test case tagging."""

    @keyword("I add tags ${tags} to the test case")
    def add_tags_to_case(self, tags: str) -> None:
        tag_list = _split(tags)
        response = self.client.put(
            f"/cases/{self.current_case_id}", json={"tags": tag_list},
        )
        assert response.status_code == 200, response.text

    @keyword("the test case should have tags ${tags}")
    def case_should_have_tags(self, tags: str) -> None:
        expected = sorted(_split(tags))
        response = self.client.get(f"/cases/{self.current_case_id}")
        actual = sorted(response.json().get("tags") or [])
        assert actual == expected, f"Expected tags {expected}, got {actual}"


def _split(values: str) -> list[str]:
    return [tag.strip() for tag in values.split(",") if tag.strip()]
