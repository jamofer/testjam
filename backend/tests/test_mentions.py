"""Tests for the shared mention parser."""
from testjam.services.mentions import parse, usernames


def test_user_mention_basic():
    result = parse("hey @alice can you check this")
    assert [(m.kind, m.slug) for m in result] == [("user", "alice")]


def test_email_does_not_trigger_user_mention():
    result = parse("contact admin@example.com about it")
    assert result == []


def test_bug_reference():
    result = parse("duplicate of #42")
    assert [(m.kind, m.id) for m in result] == [("bug", 42)]


def test_execution_reference():
    result = parse("see run !17 results")
    assert [(m.kind, m.id) for m in result] == [("execution", 17)]


def test_result_composite():
    result = parse("failed in !17/91")
    only = result[0]
    assert only.kind == "result"
    assert only.id == 17
    assert only.sub_ids == (91,)


def test_step_result_composite():
    result = parse("step diff: !17/91/3 vs !17/91/4")
    kinds = [(m.kind, m.id, m.sub_ids) for m in result]
    assert kinds == [
        ("step_result", 17, (91, 3)),
        ("step_result", 17, (91, 4)),
    ]


def test_case_reference():
    result = parse("covered by ~91")
    assert [(m.kind, m.id) for m in result] == [("case", 91)]


def test_mentions_inside_code_block_are_ignored():
    body = "before @alice\n```\nlook at #42 here\n```\nafter @bob"
    result = parse(body)
    assert [m.slug for m in result if m.kind == "user"] == ["alice", "bob"]
    assert all(m.kind != "bug" for m in result)


def test_mentions_inside_inline_code_are_ignored():
    result = parse("the `@admin` tag and a real @alice")
    assert [m.slug for m in result if m.kind == "user"] == ["alice"]


def test_dedupes_repeated_tokens():
    result = parse("@alice ping @alice again, see #42 and #42 too")
    kinds = [(m.kind, m.slug or m.id) for m in result]
    assert kinds == [("user", "alice"), ("bug", 42)]


def test_heading_hash_does_not_match():
    result = parse("# Title\nbody #42")
    assert [(m.kind, m.id) for m in result] == [("bug", 42)]


def test_usernames_helper():
    assert usernames("ping @alice and @bob_92") == ["alice", "bob_92"]
