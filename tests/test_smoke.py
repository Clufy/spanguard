import spanguard


def test_version_is_string() -> None:
    assert isinstance(spanguard.__version__, str)
    assert spanguard.__version__
