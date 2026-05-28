from app.agents.tools import calculator


def test_calculator_basic():
    assert "= 14" in calculator("2 + 3 * 4")


def test_calculator_power():
    assert "= 1024" in calculator("2 ** 10")


def test_calculator_rejects_unsafe():
    out = calculator("__import__('os').system('echo bad')")
    assert "error" in out.lower()
