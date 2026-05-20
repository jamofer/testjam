"""Tests for the ``cf:`` Robot tag parser."""
from testjam_listener.listener import _parse_cf_tags


def test_single_value_tag_becomes_string():
    assert _parse_cf_tags(["cf:priority=p0"]) == {"priority": "p0"}


def test_comma_separated_value_becomes_list():
    assert _parse_cf_tags(["cf:envs=browser,mobile"]) == {
        "envs": ["browser", "mobile"],
    }


def test_non_cf_tags_are_ignored():
    assert _parse_cf_tags(["smoke", "regression", "cf:area=auth"]) == {
        "area": "auth",
    }


def test_tag_without_equals_is_skipped():
    assert _parse_cf_tags(["cf:standalone"]) == {}


def test_tag_with_empty_key_or_value_is_skipped():
    assert _parse_cf_tags(["cf:=value", "cf:key="]) == {}


def test_value_containing_equals_keeps_the_remainder():
    assert _parse_cf_tags(["cf:url=http://x?a=1"]) == {
        "url": "http://x?a=1",
    }


def test_later_tags_overwrite_earlier_for_same_key():
    assert _parse_cf_tags(["cf:priority=p1", "cf:priority=p0"]) == {
        "priority": "p0",
    }


def test_whitespace_is_trimmed():
    assert _parse_cf_tags(["cf:  priority  =  p0  "]) == {"priority": "p0"}
