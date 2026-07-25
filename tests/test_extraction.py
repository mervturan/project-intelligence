from services.extraction import extract_note_intelligence


def test_extracts_decision_and_action():
    text = (
        "We agreed to use SQuAD as the main dataset. "
        "I need to test Qwen 1.5B before Friday."
    )
    result = extract_note_intelligence(text)
    assert result["decisions"]
    assert result["actions"]
    assert result["actions"][0]["deadline"].lower() == "friday"
