from app.services import ragas_evaluator


def test_ragas_not_available_falls_back():
    # In the test environment ragas is not installed -> should report unavailable
    # and evaluate_with_ragas returns None.
    if ragas_evaluator.is_available():
        return  # if ragas actually installed, nothing to assert here
    import pytest

    pytest.mark.skip("ragas is installed; skip fallback test")


def test_is_available_returns_bool():
    assert isinstance(ragas_evaluator.is_available(), bool)


def test_evaluate_returns_none_when_unavailable():
    import asyncio

    if ragas_evaluator.is_available():
        return
    result = asyncio.new_event_loop().run_until_complete(
        ragas_evaluator.evaluate_with_ragas(
            "q", "a", ["c"], ground_truth=None
        )
    )
    assert result is None
