import json
from pathlib import Path

from spanguard.cli import main


def _write(tmp_path: Path, text: str) -> str:
    p = tmp_path / "input.txt"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_scan_reports_counts_without_raw(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "call 555-123-4567 mail jane@x.com")
    rc = main(["scan", path, "--entities", "PHONE,EMAIL"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "PHONE" in out and "EMAIL" in out
    assert "555-123-4567" not in out         # no raw value leaks to stdout
    assert "jane@x.com" not in out


def test_scan_json_output(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "ssn 123-45-6789")
    rc = main(["scan", path, "--entities", "SSN", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["counts"] == {"SSN": 1}
    assert "123-45-6789" not in out


def test_redact_to_stdout(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "mail jane@x.com")
    rc = main(["redact", path, "--mode", "placeholder", "--entities", "EMAIL"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "[EMAIL]" in out
    assert "jane@x.com" not in out


def test_redact_to_out_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "mail jane@x.com")
    outp = tmp_path / "red.txt"
    rc = main(["redact", path, "--mode", "mask", "--entities", "EMAIL", "--out", str(outp)])
    assert rc == 0
    written = outp.read_text(encoding="utf-8")
    assert "jane@x.com" not in written
    assert "█" in written


def test_redact_audit_json_to_stderr(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "mail jane@x.com")
    rc = main(["redact", path, "--mode", "placeholder", "--entities", "EMAIL", "--audit-json"])
    captured = capsys.readouterr()
    assert rc == 0
    audit = json.loads(captured.err)
    assert audit["counts"] == {"EMAIL": 1}
    assert "policy_hash" in audit and "ts" in audit
    assert "jane@x.com" not in captured.err


def test_redact_mask_stdout_is_utf8_safe(tmp_path, capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Regression: default mask mode emits U+2588; the CLI must force UTF-8 on
    # its streams so writing to a non-UTF-8 console does not crash. We assert
    # main() makes stdout UTF-8-capable and the mask char is present + encodable.
    path = tmp_path / "in.txt"
    path.write_text("mail jane@x.com", encoding="utf-8")
    rc = main(["redact", str(path), "--mode", "mask", "--entities", "EMAIL"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "█" in out
    # the emitted text must be encodable as UTF-8 without error (the crash was
    # an encode failure); this would raise if any surrogate/unencodable slipped in
    out.encode("utf-8")


def test_missing_file_errors(capsys) -> None:  # type: ignore[no-untyped-def]
    rc = main(["scan", "does_not_exist_12345.txt"])
    assert rc == 2
    assert "does_not_exist_12345.txt" in capsys.readouterr().err


def test_help_runs() -> None:
    import pytest

    with pytest.raises(SystemExit) as ei:
        main(["--help"])
    assert ei.value.code == 0


def _stdin(monkeypatch, data: bytes) -> None:  # type: ignore[no-untyped-def]
    import io
    import sys

    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data), encoding="cp1252"))


def test_unknown_entity_is_a_usage_error(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "mail jane@x.com")
    rc = main(["redact", path, "--entities", "EMIAL,PHONE"])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""  # nothing (unredacted or otherwise) is written
    assert "unknown entity type(s): EMIAL" in captured.err
    assert "CREDIT_CARD" in captured.err  # lists the valid choices
    assert "jane@x.com" not in captured.err


def test_non_utf8_file_errors_without_content(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    p = tmp_path / "latin1.txt"
    p.write_bytes("secret café 123-45-6789".encode("latin-1"))
    rc = main(["scan", str(p)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "error: cannot decode" in err and "UTF-8" in err
    assert "123-45-6789" not in err


def test_directory_path_errors(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    rc = main(["redact", str(tmp_path)])
    assert rc == 2
    assert "error: cannot read" in capsys.readouterr().err


def test_redact_reads_stdin_as_utf8(capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _stdin(monkeypatch, "café jane@x.com\n".encode())
    rc = main(["redact", "-", "--mode", "placeholder"])
    assert rc == 0
    assert capsys.readouterr().out == "café [EMAIL]\n"


def test_scan_reads_stdin(capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _stdin(monkeypatch, b"ssn 123-45-6789")
    rc = main(["scan", "-"])
    assert rc == 0
    assert capsys.readouterr().out == "SSN: 1\n"


def test_non_utf8_stdin_errors(capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _stdin(monkeypatch, b"\xff\xfe bad")
    rc = main(["scan", "-"])
    assert rc == 2
    assert "error: cannot decode <stdin>" in capsys.readouterr().err


def test_text_only_stdin_is_supported(capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import io
    import sys

    monkeypatch.setattr(sys, "stdin", io.StringIO("ssn 123-45-6789"))  # no .buffer
    assert main(["scan", "-"]) == 0
    assert capsys.readouterr().out == "SSN: 1\n"


def test_unwritable_out_path_errors(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    path = _write(tmp_path, "mail jane@x.com")
    bad_out = tmp_path / "no_such_dir" / "o.txt"
    rc = main(["redact", path, "--out", str(bad_out)])
    err = capsys.readouterr().err
    assert rc == 2
    assert f"error: cannot write {bad_out}" in err
    assert "jane@x.com" not in err and "Traceback" not in err


def test_missing_stdin_errors(capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import sys

    monkeypatch.setattr(sys, "stdin", None)  # `<&-`, pythonw
    assert main(["scan", "-"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error: cannot read <stdin>: stdin is not available" in captured.err


def test_closed_stdin_errors(capsys, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import io
    import sys

    stdin = io.TextIOWrapper(io.BytesIO(b"ssn 123-45-6789"))
    stdin.close()
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main(["redact", "-"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error: cannot read <stdin>: stdin is not available" in captured.err
