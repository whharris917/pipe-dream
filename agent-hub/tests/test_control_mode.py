"""Unit tests for tmux control mode parsing in pty_manager.

Tests the module-level helpers that decode tmux control mode protocol:
    - _decode_octal: octal escape sequence → raw bytes
    - _decode_control_output: %output line → decoded bytes
    - _encode_send_keys: raw bytes → send-keys -H hex command
"""

from agent_hub.pty_manager import (
    _decode_octal,
    _decode_control_output,
    _encode_send_keys,
)


# ---------------------------------------------------------------------------
# _decode_octal
# ---------------------------------------------------------------------------

class TestDecodeOctal:
    """Tests for octal escape decoding."""

    def test_printable_passthrough(self):
        """Printable ASCII passes through unchanged."""
        assert _decode_octal("hello world") == b"hello world"

    def test_empty_string(self):
        assert _decode_octal("") == b""

    def test_esc_sequence(self):
        r"""\\033 decodes to ESC (0x1b)."""
        assert _decode_octal("\\033[1m") == b"\x1b[1m"

    def test_cr_lf(self):
        r"""\\015\\012 decodes to CR LF."""
        assert _decode_octal("\\015\\012") == b"\r\n"

    def test_backslash_literal(self):
        r"""\\134 decodes to backslash."""
        assert _decode_octal("\\134") == b"\\"

    def test_tab(self):
        r"""\\011 decodes to TAB."""
        assert _decode_octal("\\011") == b"\t"

    def test_mixed_content(self):
        """Mix of printable text and escaped control chars."""
        assert _decode_octal("\\033[1mBold\\033[0m\\015\\012") == (
            b"\x1b[1mBold\x1b[0m\r\n"
        )

    def test_consecutive_escapes(self):
        """Multiple escape sequences back to back."""
        assert _decode_octal("\\033\\033\\033") == b"\x1b\x1b\x1b"

    def test_trailing_backslash_no_octal(self):
        r"""Backslash at end without 3 following chars passes through."""
        # \\ at end of string with fewer than 3 chars following
        assert _decode_octal("abc\\") == b"abc\\"

    def test_backslash_with_non_octal(self):
        r"""Backslash followed by non-octal digits passes through."""
        assert _decode_octal("\\xyz") == b"\\xyz"

    def test_null_byte(self):
        r"""\\000 decodes to null byte."""
        assert _decode_octal("\\000") == b"\x00"

    def test_max_byte(self):
        r"""\\377 decodes to 0xFF."""
        assert _decode_octal("\\377") == b"\xff"

    def test_unicode_passthrough(self):
        """Non-ASCII Unicode chars (e.g. box-drawing) re-encode to UTF-8."""
        # U+2502 BOX DRAWINGS LIGHT VERTICAL = 3-byte UTF-8: e2 94 82
        assert _decode_octal("\u2502") == b"\xe2\x94\x82"

    def test_mixed_unicode_and_escapes(self):
        """Mix of octal escapes and raw Unicode."""
        assert _decode_octal("\\033[1m\u2502\\033[0m") == (
            b"\x1b[1m\xe2\x94\x82\x1b[0m"
        )


# ---------------------------------------------------------------------------
# _decode_control_output
# ---------------------------------------------------------------------------

class TestDecodeControlOutput:
    """Tests for control mode %output line parsing."""

    def test_simple_output(self):
        """Basic %output line with text content."""
        line = "%output %0 hello world"
        assert _decode_control_output(line) == b"hello world"

    def test_output_with_escapes(self):
        """Output line with octal-escaped control characters."""
        line = "%output %0 \\033[1mBold\\033[0m\\015\\012"
        assert _decode_control_output(line) == b"\x1b[1mBold\x1b[0m\r\n"

    def test_non_output_begin(self):
        """%begin lines return None."""
        assert _decode_control_output("%begin 1234 0") is None

    def test_non_output_end(self):
        """%end lines return None."""
        assert _decode_control_output("%end 1234 0") is None

    def test_non_output_session_changed(self):
        """%session-changed lines return None."""
        assert _decode_control_output("%session-changed $0 agent") is None

    def test_non_output_exit(self):
        """%exit lines return None."""
        assert _decode_control_output("%exit") is None

    def test_empty_line(self):
        """Empty line returns None."""
        assert _decode_control_output("") is None

    def test_output_no_payload(self):
        """%output with pane ID but no payload returns empty bytes."""
        assert _decode_control_output("%output %0") == b""

    def test_output_different_pane(self):
        """%output with different pane IDs."""
        line = "%output %3 data"
        assert _decode_control_output(line) == b"data"

    def test_random_text(self):
        """Arbitrary text that doesn't start with % returns None."""
        assert _decode_control_output("some random text") is None

    def test_percent_but_not_output(self):
        """%something-else returns None."""
        assert _decode_control_output("%layout-change blah") is None


# ---------------------------------------------------------------------------
# _encode_send_keys
# ---------------------------------------------------------------------------

class TestEncodeSendKeys:
    """Tests for send-keys hex encoding."""

    def test_simple_text(self):
        """ASCII text is hex-encoded."""
        result = _encode_send_keys(b"hello")
        assert result == b"send-keys -t agent -H 68 65 6c 6c 6f\n"

    def test_single_byte(self):
        """Single byte."""
        result = _encode_send_keys(b"a")
        assert result == b"send-keys -t agent -H 61\n"

    def test_enter_key(self):
        """Carriage return (Enter key)."""
        result = _encode_send_keys(b"\r")
        assert result == b"send-keys -t agent -H 0d\n"

    def test_escape_key(self):
        """ESC byte."""
        result = _encode_send_keys(b"\x1b")
        assert result == b"send-keys -t agent -H 1b\n"

    def test_arrow_key_sequence(self):
        """Arrow up: ESC [ A."""
        result = _encode_send_keys(b"\x1b[A")
        assert result == b"send-keys -t agent -H 1b 5b 41\n"

    def test_ctrl_c(self):
        """Ctrl+C (0x03)."""
        result = _encode_send_keys(b"\x03")
        assert result == b"send-keys -t agent -H 03\n"

    def test_empty_input(self):
        """Empty input produces command with no hex bytes."""
        result = _encode_send_keys(b"")
        assert result == b"send-keys -t agent -H \n"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
