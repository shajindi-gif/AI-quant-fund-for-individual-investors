from pathlib import Path

def test_harness_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / 'README_FOR_AGENTS.md').exists()
    assert (root / 'RUNBOOK.md').exists()
    assert (root / 'AGENT_CARDS.md').exists()
    assert (root / 'ACCEPTANCE_CRITERIA.md').exists()

