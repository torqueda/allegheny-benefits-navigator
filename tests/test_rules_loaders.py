from src.loaders.rules import load_eligibility_rules, load_priority_heuristics, load_program_sources


def test_load_eligibility_rules_returns_list() -> None:
    rules = load_eligibility_rules("data/rules_source")
    assert isinstance(rules, list)
    assert len(rules) > 0


def test_load_priority_heuristics_returns_list() -> None:
    heuristics = load_priority_heuristics("data/rules_source")
    assert isinstance(heuristics, list)
    assert len(heuristics) > 0


def test_load_program_sources_returns_list() -> None:
    sources = load_program_sources("data/rules_source")
    assert isinstance(sources, list)
    # May be empty if CSV not present, but test structure