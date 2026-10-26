"""M2 schema strictness: explicit dicts, additionalProperties false everywhere."""
from proof.roles.builder import BUILDER_SCHEMA
from proof.roles.reviser import FREEFORM_REVISION_SCHEMA, REVISER_SCHEMA
from proof.roles.reviewer import CLAIM_SCHEMA, REVIEWER_SCHEMA
from proof.roles.self_refine import SELF_REFINE_SCHEMA, SELF_TESTS_SCHEMA


def _walk(node, path="root"):
    if isinstance(node, dict):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, f"object at {path} lacks additionalProperties false: {node}"
            props = node.get("properties", {})
            assert set(node.get("required", [])) == set(props), f"object at {path} required != properties"
        for k, v in node.items():
            _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, f"{path}[{i}]")


def test_all_role_schemas_strict_everywhere():
    for schema in (BUILDER_SCHEMA, REVIEWER_SCHEMA, CLAIM_SCHEMA, REVISER_SCHEMA,
                   FREEFORM_REVISION_SCHEMA, SELF_TESTS_SCHEMA, SELF_REFINE_SCHEMA):
        _walk(schema)


def test_reviewer_schema_limits_and_enums():
    assert REVIEWER_SCHEMA["properties"]["claims"]["maxItems"] == 5
    assert REVIEWER_SCHEMA["properties"]["verdict"]["enum"] == ["defects_found", "no_proven_defects"]
    assert CLAIM_SCHEMA["properties"]["severity"]["enum"] == ["critical", "major", "minor"]


def test_reviewer_prompt_proof_rule_language():
    text = open("proof/roles/prompts/reviewer.md", encoding="utf-8").read()
    assert "Only report defects you can make executable" in text
    assert "A claim whose test passes" in text and "discarded" in text
    assert "exact spec" in text and "spec_reference" in text


def test_freeform_prompt_no_tests():
    text = open("proof/roles/prompts/reviewer_freeform.md", encoding="utf-8").read()
    assert "Do NOT write tests" in text
    assert "no proof rule" in text.lower()
