from open_align.core import make_greeting

def test_greeting_contains_name():
    assert "Juan" in make_greeting("Juan")
