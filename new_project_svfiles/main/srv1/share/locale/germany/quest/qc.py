#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════
# qc.py — Python port of Metin2's quest compiler (qc.cc)
#
# Byte-equivalent to qc.exe output, with ENABLE_NUMBER_ADJUSTMENT applied by
# default (fixes large-integer literals emitting as scientific notation).
# Single file, Python 3.8+, stdlib only. Runs on Windows and FreeBSD.
#
# Written by martysama0134.
# Licensed under the MIT License — see LICENSE for details.
# ═══════════════════════════════════════════════════════════════════════════
#
# Reading guide
# -------------
# Pipeline: .quest source → Lexer → QCParser (state machine) → emit() →
# files under object/.
#
# If you are reading this file for the first time, skim top-to-bottom:
# Section 0 holds feature flags, Section 1 the exception types, Section 2
# the CRC32 routine used by the emitter, Section 3 the byte-oriented Lua 5.0
# lexer, Section 4 a grammar-only Lua parser (catches typos in user
# with-conditions and when-bodies), Section 5 the qc-specific state machine
# that turns .quest syntax into per-trigger Lua scripts, Section 6 the
# emitter that writes those scripts into object/, and Section 7 the CLI.
#
# For contributors: any change that affects output bytes must stay in
# lockstep with qc.cc. Inline comments carry `qc.cc:<lineno>` /
# `llex.c:<lineno>` references back to the C++ source — do not paraphrase
# these away.

"""qc — Metin2 quest compiler, Python port (byte-equivalent to qc.exe)."""

import argparse
import io
import math
import os
import sys
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════
# Section 0: Feature flags
# ═══════════════════════════════════════════════════════════════════════════
#
# Three compile-time switches and one module-level version string.
#
# ENABLE_PARSING_CHECK and ENABLE_NUMBER_ADJUSTMENT are the ones a community
# maintainer might realistically flip. The third (ENABLE_WHEN_PARENTHESIS)
# mirrors a qc.cc flag and is here for parity; leave it True unless you are
# reproducing an older qc.exe build.
#
# The environment variable QC_NO_NUMBER_ADJUSTMENT=1 forces the
# scientific-notation behaviour of stock qc.exe for integer-valued doubles.
# The byte-equivalence test harness uses it; normal users do not need it.

__version__ = "1.0.1"

ENABLE_PARSING_CHECK = True        # Lua 5.0 syntax validation of emitted snippets
ENABLE_NUMBER_ADJUSTMENT = True    # integer-valued doubles emit as integers
ENABLE_WHEN_PARENTHESIS = True     # qc.cc ENABLE_WHEN_PARENTHESIS

# Env-var override (test harness uses this to match vanilla qc.exe output).
if os.environ.get("QC_NO_NUMBER_ADJUSTMENT") == "1":
    ENABLE_NUMBER_ADJUSTMENT = False

# ═══════════════════════════════════════════════════════════════════════════
# Section 1: Errors
# ═══════════════════════════════════════════════════════════════════════════
#
# All compile-time errors raise a QCError subclass carrying (filename, line,
# message). The three subclasses distinguish origin: LexerError from
# Section 3, QCParseError from Section 5 (.quest state machine), and
# QCSyntaxError from Section 4 (the embedded Lua syntax check).

class QCError(Exception):
    """Base class for compile-time errors. Carries filename, line, and message."""

    def __init__(self, filename: str, line: int, message: str):
        super().__init__(f"{filename}:{line}: {message}")
        self.filename = filename
        self.line = line
        self.message = message

class LexerError(QCError):
    """Raised by the Lexer on malformed source bytes."""

class QCParseError(QCError):
    """Raised by QCParser when .quest structure is wrong."""

class QCSyntaxError(QCError):
    """Raised by the embedded Lua 5.0 syntax check on malformed snippets."""

# ═══════════════════════════════════════════════════════════════════════════
# Section 2: CRC32 (zlib-compatible; identical table to crc32.cc)
# ═══════════════════════════════════════════════════════════════════════════
#
# CRC32/IEEE, byte-identical to crc32.cc's get_crc32(). Used by Section 6 to
# hash state names into the integer IDs that appear in
# object/state/<quest>. Pinning the algorithm to zlib's polynomial and table
# means state IDs stay stable across qc.py versions and against qc.exe — a
# quest compiled today references the same state numbers as one compiled
# years ago on a different build.
#
# The signed-int formatting quirk (state IDs >= 0x80000000 emit as negative
# decimals) lives in _emit_state_file, not here — see Section 6.

def _build_crc32_table() -> list:
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (0xEDB88320 ^ (c >> 1)) if (c & 1) else (c >> 1)
        table.append(c)
    return table

_CRC32_TABLE = _build_crc32_table()

def crc32(data: bytes) -> int:
    """CRC32/IEEE — byte-identical to crc32.cc's get_crc32()."""
    crc = 0xFFFFFFFF
    for b in data:
        crc = _CRC32_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF

# ═══════════════════════════════════════════════════════════════════════════
# Section 3: Lexer (close port of liblua/5.0/src/llex.c)
# ═══════════════════════════════════════════════════════════════════════════
#
# Byte-oriented Lua 5.0 lexer, close port of liblua/5.0/src/llex.c. Byte
# (not text) because Lua 5.0 itself lexes bytes and we must match that
# behaviour exactly — identifiers can contain Latin-1 bytes (>=0xA0) in the
# custom Lua build Metin2 ships, and strings pass through arbitrary bytes
# between quotes.
#
# Three qc-specific deviations from stock Lua are worth knowing:
#   - `begin` is accepted as a synonym for `do` (both map to TK_DO).
#   - `!=` is accepted as a synonym for `~=`, and bare `!` for `not`.
#   - Identifiers may contain bytes >=0xA0 (Latin-1), not just ASCII.
# Each deviation has an inline llex.c line reference where it applies.

# Token kind constants — same ordering as llex.h enum RESERVED (FIRST_RESERVED=257).
FIRST_RESERVED = 257
(TK_AND, TK_BREAK, TK_DO, TK_ELSE, TK_ELSEIF, TK_END, TK_FALSE, TK_FOR,
 TK_FUNCTION, TK_IF, TK_IN, TK_LOCAL, TK_NIL, TK_NOT, TK_OR, TK_REPEAT,
 TK_RETURN, TK_THEN, TK_TRUE, TK_UNTIL, TK_WHILE,
 TK_QUEST, TK_STATE, TK_WITH, TK_WHEN, TK_DEFINE, TK_BEGIN,
 TK_NAME, TK_CONCAT, TK_DOTS, TK_EQ, TK_GE, TK_LE, TK_NE,
 TK_NUMBER, TK_STRING, TK_EOS) = range(FIRST_RESERVED, FIRST_RESERVED + 37)

# Identifier → reserved token. Must match llex.c's luaX_tokens[] order/values.
_RESERVED_WORDS = {
    b"and":      TK_AND,     b"break":    TK_BREAK,    b"do":     TK_DO,
    b"else":     TK_ELSE,    b"elseif":   TK_ELSEIF,   b"end":    TK_END,
    b"false":    TK_FALSE,   b"for":      TK_FOR,      b"function": TK_FUNCTION,
    b"if":       TK_IF,      b"in":       TK_IN,       b"local":  TK_LOCAL,
    b"nil":      TK_NIL,     b"not":      TK_NOT,      b"or":     TK_OR,
    b"repeat":   TK_REPEAT,  b"return":   TK_RETURN,   b"then":   TK_THEN,
    b"true":     TK_TRUE,    b"until":    TK_UNTIL,    b"while":  TK_WHILE,
    b"quest":    TK_QUEST,   b"state":    TK_STATE,    b"with":   TK_WITH,
    b"when":     TK_WHEN,    b"define":   TK_DEFINE,   b"begin":  TK_DO,
}
# qc.cc's custom Lua 5.0 makes 'begin' and 'do' aliases: both map to TK_DO.
# See liblua/5.0/src/llex.c: token_preserved[] mechanism. TK_BEGIN constant
# is kept for llex.h enum parity but no source word lexes to it.

@dataclass
class Token:
    """One token produced by the Lexer: kind plus optional payload."""

    kind: int
    str_val: Optional[bytes] = None   # for TK_NAME, TK_STRING (decoded bytes)
    num_val: Optional[float] = None   # for TK_NUMBER

_EOZ = -1  # llex.c's end-of-input sentinel

class Lexer:
    """Byte-oriented Lua 5.0 lexer with qc extensions.

    Close port of llex.c. Input is a binary stream; output is a sequence of
    Token objects produced via next() / lookahead(). qc extensions:
    `begin` aliases `do`, `!` / `!=` alias `not` / `~=`, and identifiers may
    contain Latin-1 bytes >=0xA0.
    """

    def __init__(self, stream, source_name: str):
        self._stream = stream
        self.source = source_name
        self.linenumber = 1
        self.lastline = 1
        self.t = Token(TK_EOS)
        self.lookahead_t = Token(TK_EOS)
        self._buf = b""      # accumulator (llex.c's Mbuffer *buff)
        self._current = self._read_byte()   # llex.c's ls->current

    def _read_byte(self) -> int:
        b = self._stream.read(1)
        return b[0] if b else _EOZ

    def _advance(self) -> int:
        self._current = self._read_byte()
        return self._current

    def _save(self, b: int) -> None:
        self._buf += bytes([b]) if b >= 0 else b""

    def _save_and_next(self) -> int:
        self._save(self._current)
        return self._advance()

    def _error(self, msg: str):
        raise LexerError(self.source, self.linenumber, msg)

    def next(self) -> None:
        self.lastline = self.linenumber
        if self.lookahead_t.kind != TK_EOS:
            self.t = self.lookahead_t
            self.lookahead_t = Token(TK_EOS)
            return
        self.t = self._lex()

    def lookahead(self) -> None:
        assert self.lookahead_t.kind == TK_EOS
        self.lookahead_t = self._lex()

    def _lex(self) -> Token:
        while True:
            c = self._current
            if c == _EOZ:
                return Token(TK_EOS)
            if c in (0x20, 0x09, 0x0B, 0x0C):
                self._advance(); continue
            if c == 0x0A or c == 0x0D:
                self._inclinenumber(); continue

            # comments
            if c == ord('-'):
                self._advance()
                if self._current != ord('-'):
                    return Token(ord('-'))
                self._advance()
                # block comment '--[[' or '--[=[' ... ']=]' ']]'
                if self._current == ord('['):
                    sep = self._skip_sep()
                    if sep >= 0:
                        self._read_long_string(sep, is_string=False)
                        continue
                # line comment: consume until newline or EOZ
                while self._current != _EOZ and self._current != 0x0A and self._current != 0x0D:
                    self._advance()
                continue

            # long string '[[' or '[=[' ...
            if c == ord('['):
                sep = self._skip_sep()
                if sep >= 0:
                    return self._read_long_string(sep, is_string=True)
                return Token(ord('['))

            # strings
            if c == ord('"') or c == ord("'"):
                return self._read_string(c)

            # numbers
            if 0x30 <= c <= 0x39:
                return self._read_numeral(False)

            # dot family: '.', '..', '...', '.5'
            if c == ord('.'):
                self._advance()
                if self._current == ord('.'):
                    self._advance()
                    if self._current == ord('.'):
                        self._advance()
                        return Token(TK_DOTS)
                    return Token(TK_CONCAT)
                if 0x30 <= self._current <= 0x39:
                    self._buf = b"."
                    return self._read_numeral(True)
                return Token(ord('.'))

            # two-char operators
            if c == ord('='):
                self._advance()
                if self._current == ord('='):
                    self._advance(); return Token(TK_EQ)
                return Token(ord('='))
            if c == ord('<'):
                self._advance()
                if self._current == ord('='):
                    self._advance(); return Token(TK_LE)
                return Token(ord('<'))
            if c == ord('>'):
                self._advance()
                if self._current == ord('='):
                    self._advance(); return Token(TK_GE)
                return Token(ord('>'))
            if c == ord('~'):
                self._advance()
                if self._current == ord('='):
                    self._advance(); return Token(TK_NE)
                return Token(ord('~'))
            # llex.c:387 — '!=' is TK_NE, bare '!' is TK_NOT (C-style aliases).
            if c == ord('!'):
                self._advance()
                if self._current == ord('='):
                    self._advance(); return Token(TK_NE)
                return Token(TK_NOT)

            # identifiers & keywords
            if self._is_ident_start(c):
                return self._read_identifier()

            # any other single byte: return as its own integer token (parens, brackets, '+', '*', ';', etc.)
            self._advance()
            return Token(c)

    def _read_numeral(self, has_leading_dot: bool) -> Token:
        if not has_leading_dot:
            self._buf = b""
            # first char (digit) still in current; consume digits
            while 0x30 <= self._current <= 0x39:
                self._save_and_next()
            # hex prefix: only if value so far is b"0" and next is 'x' or 'X'
            if self._buf == b"0" and self._current in (ord('x'), ord('X')):
                self._save_and_next()
                while (0x30 <= self._current <= 0x39) or \
                      (0x41 <= self._current <= 0x46) or \
                      (0x61 <= self._current <= 0x66):
                    self._save_and_next()
                s = self._buf
                self._buf = b""
                try:
                    return Token(TK_NUMBER, num_val=float(int(s, 16)))
                except ValueError:
                    self._error("malformed number")
            if self._current == ord('.'):
                self._save_and_next()
        # fractional part
        while 0x30 <= self._current <= 0x39:
            self._save_and_next()
        # exponent
        if self._current in (ord('e'), ord('E')):
            self._save_and_next()
            if self._current in (ord('+'), ord('-')):
                self._save_and_next()
            while 0x30 <= self._current <= 0x39:
                self._save_and_next()
        s = self._buf
        self._buf = b""
        try:
            return Token(TK_NUMBER, num_val=float(s.decode("ascii")))
        except ValueError:
            self._error("malformed number")

    def _read_string(self, quote: int) -> Token:
        self._buf = b""
        self._advance()  # consume opening quote
        while self._current != quote:
            c = self._current
            if c == _EOZ:
                self._error("unfinished string")
            if c == 0x0A or c == 0x0D:
                self._error("unfinished string")
            if c == 0x5C:                        # backslash
                self._advance()
                nxt = self._current
                if nxt == ord('a'):   self._buf += b"\a"; self._advance()
                elif nxt == ord('b'): self._buf += b"\b"; self._advance()
                elif nxt == ord('f'): self._buf += b"\f"; self._advance()
                elif nxt == ord('n'): self._buf += b"\n"; self._advance()
                elif nxt == ord('r'): self._buf += b"\r"; self._advance()
                elif nxt == ord('t'): self._buf += b"\t"; self._advance()
                elif nxt == ord('v'): self._buf += b"\v"; self._advance()
                elif nxt == ord('\\'): self._buf += b"\\"; self._advance()
                elif nxt == ord('"'):  self._buf += b'"'; self._advance()
                elif nxt == ord("'"):  self._buf += b"'"; self._advance()
                elif nxt == 0x0A or nxt == 0x0D:
                    self._buf += b"\n"
                    self._inclinenumber()
                elif nxt == _EOZ:
                    pass  # handled on next loop iter
                elif 0x30 <= nxt <= 0x39:        # \ddd (1-3 decimal digits)
                    val = 0
                    i = 0
                    while i < 3 and 0x30 <= self._current <= 0x39:
                        val = val * 10 + (self._current - 0x30)
                        self._advance()
                        i += 1
                    if val > 255:
                        self._error("escape sequence too large")
                    self._buf += bytes([val])
                else:
                    # Lua 5.0: unknown escape is an error
                    self._error("invalid escape sequence")
            else:
                self._buf += bytes([c])
                self._advance()
        self._advance()  # consume closing quote
        s = self._buf
        self._buf = b""
        return Token(TK_STRING, str_val=s)

    def _inclinenumber(self) -> None:
        old = self._current
        assert old == 0x0A or old == 0x0D
        self._advance()
        if self._current in (0x0A, 0x0D) and self._current != old:
            self._advance()
        self.linenumber += 1

    @staticmethod
    def _is_ident_start(c: int) -> bool:
        # llex.c:425 — isalpha || '_' || current >= 0xa0 (Latin-1 extended bytes).
        return c == 0x5F or (0x41 <= c <= 0x5A) or (0x61 <= c <= 0x7A) or c >= 0xA0

    @staticmethod
    def _is_ident_cont(c: int) -> bool:
        return Lexer._is_ident_start(c) or (0x30 <= c <= 0x39)  # + 0-9

    def _read_identifier(self) -> Token:
        self._buf = b""
        while self._current != _EOZ and self._is_ident_cont(self._current):
            self._save_and_next()
        ident = self._buf
        self._buf = b""
        kind = _RESERVED_WORDS.get(ident, TK_NAME)
        if kind == TK_NAME:
            return Token(TK_NAME, str_val=ident)
        return Token(kind)

    def _skip_sep(self) -> int:
        """Count the '=' signs between '[' and '['. Return count, or -1 if not a long bracket."""
        count = 0
        start = self._current  # should be '['
        assert start == ord('[')
        self._advance()
        while self._current == ord('='):
            self._advance()
            count += 1
        if self._current == ord('['):
            return count
        return -1

    def _read_long_string(self, sep: int, is_string: bool) -> Token:
        """sep == number of '=' signs. is_string=True → return TK_STRING, False → discard (for comments)."""
        self._buf = b""
        self._advance()  # consume opening '['
        if self._current == 0x0A or self._current == 0x0D:
            self._inclinenumber()
        while True:
            c = self._current
            if c == _EOZ:
                self._error("unfinished long string" if is_string else "unfinished long comment")
            if c == ord(']'):
                # check for matching close
                self._advance()
                count = 0
                while self._current == ord('=') and count < sep:
                    self._advance()
                    count += 1
                if count == sep and self._current == ord(']'):
                    self._advance()
                    s = self._buf
                    self._buf = b""
                    return Token(TK_STRING, str_val=s) if is_string else Token(TK_EOS)
                # not a close — put back what we read
                self._buf += b"]"
                self._buf += b"=" * count
                continue
            if c == 0x0A or c == 0x0D:
                self._buf += b"\n"
                self._inclinenumber()
                continue
            self._buf += bytes([c])
            self._advance()

def format_number(val: float) -> bytes:
    """Emit a Lua number as bytes.

    Two modes:
    - ENABLE_NUMBER_ADJUSTMENT = True (default, production):
        * Integer-valued doubles emit as "1234567890" (no decimal point).
        * Non-integer doubles emit via repr(): shortest round-trip form,
          so "0.9" stays "0.9" (not "0.90000000000000002"), and values
          that truly require more digits (e.g. 0.1+0.2) print faithfully.
    - ENABLE_NUMBER_ADJUSTMENT = False: match vanilla qc.exe's cout default
      (std::defaultfloat << setprecision(6) → Python %.6g). Exposed for
      byte-equivalence testing against a qc.exe build without the fix.
    """
    if ENABLE_NUMBER_ADJUSTMENT:
        if math.isfinite(val) and val.is_integer():
            return f"{val:.0f}".encode("ascii")
        # repr() gives the shortest decimal that round-trips to this double.
        return repr(val).encode("ascii")
    # C++ cout default: defaultfloat, precision 6 significant digits.
    return f"{val:.6g}".encode("ascii")

# Reverse map from token kind → source representation (for non-literal tokens).
# Order/values match _RESERVED_WORDS and llex.c luaX_tokens[].
_TOKEN_TEXT = {v: k for k, v in _RESERVED_WORDS.items()}
# qc.cc's luaX_token2str returns token2string[token - FIRST_RESERVED].
# token2string[2] = "begin" (for TK_DO); token2string[26] = "do" (for TK_BEGIN,
# though no source word produces TK_BEGIN). Override the dict-comprehension
# result to match this positional mapping exactly — otherwise `do` inside
# when-bodies emits as "do" but qc.exe emits "begin", breaking byte-equivalence.
#
# User-visible effect: a `do ... end` block written inside a when-body appears
# as `begin ... end` in the Lua emitted under object/, and vice versa. This is
# not a bug — the server's custom Lua accepts both spellings interchangeably.
_TOKEN_TEXT[TK_DO]     = b"begin"
_TOKEN_TEXT[TK_BEGIN]  = b"do"
_TOKEN_TEXT[TK_CONCAT] = b".."
_TOKEN_TEXT[TK_DOTS]   = b"..."
_TOKEN_TEXT[TK_EQ]     = b"=="
_TOKEN_TEXT[TK_GE]     = b">="
_TOKEN_TEXT[TK_LE]     = b"<="
_TOKEN_TEXT[TK_NE]     = b"~="

def format_token(t: Token) -> bytes:
    """Emit a token as it appeared in source. Matches qc.cc's operator<<(ostream&, Token)."""
    k = t.kind
    if k == TK_NAME:
        return t.str_val or b""
    if k == TK_STRING:
        # qc.cc: cout << '"' << getstr(ts) << '"' — no re-escaping (bug preserved)
        return b'"' + (t.str_val or b"") + b'"'
    if k == TK_NUMBER:
        return format_number(t.num_val if t.num_val is not None else 0.0)
    txt = _TOKEN_TEXT.get(k)
    if txt is not None:
        return txt
    # single-byte tokens: parens, operators, etc.
    if 0 <= k < 256:
        return bytes([k])
    raise ValueError(f"unknown token kind: {k}")

# ═══════════════════════════════════════════════════════════════════════════
# Section 4: Lua 5.0 syntax-check parser
# Close port of liblua/5.0/src/lparser.c — grammar walk only, no codegen.
# ═══════════════════════════════════════════════════════════════════════════
#
# Grammar-only Lua 5.0 parser with codegen ripped out. Exists purely to
# validate user-supplied Lua snippets — the body of a `when` clause, the
# expression after `with`, the body of a quest-local function. Typos that
# would otherwise fail at server load time fail here instead, with the
# correct filename and line number.
#
# Controlled by ENABLE_PARSING_CHECK. Turn it off only if you need to
# compile pathological sources this stricter parser rejects; the server
# runtime stays safe either way — you just lose the early warning.

class _SyntaxCheckParser:
    """Recognize the Lua 5.0 grammar. Emit nothing; raise QCSyntaxError on bad input.

    Construct over a Lexer; call chunk() to validate. Used by check_syntax()
    at the bottom of this section.
    """

    def __init__(self, lexer: "Lexer"):
        self.ls = lexer
        self.ls.next()

    def _error(self, msg: str):
        raise QCSyntaxError(self.ls.source, self.ls.linenumber, msg)

    def _check(self, kind: int, what: str):
        if self.ls.t.kind != kind:
            self._error(f"'{what}' expected")

    def _check_next(self, kind: int, what: str):
        self._check(kind, what)
        self.ls.next()

    def _testnext(self, kind: int) -> bool:
        if self.ls.t.kind == kind:
            self.ls.next()
            return True
        return False

    def _is_block_end(self) -> bool:
        k = self.ls.t.kind
        return k in (TK_ELSE, TK_ELSEIF, TK_END, TK_UNTIL, TK_EOS)

    def chunk(self):
        """chunk -> { stat [';'] }"""
        while not self._is_block_end():
            is_return = self.ls.t.kind == TK_RETURN
            self.statement()
            self._testnext(ord(';'))
            if is_return:
                break
        # caller checks EOS

    def statement(self):
        k = self.ls.t.kind
        if k == TK_IF:        self._ifstat()
        elif k == TK_WHILE:   self._whilestat()
        elif k == TK_DO:      self.ls.next(); self._block(); self._check_next(TK_END, "end")
        elif k == TK_FOR:     self._forstat()
        elif k == TK_REPEAT:  self._repeatstat()
        elif k == TK_FUNCTION: self._funcstat()
        elif k == TK_LOCAL:   self._localstat()
        elif k == TK_RETURN:  self._retstat()
        elif k == TK_BREAK:   self.ls.next()
        else:                 self._exprstat()

    def _block(self):
        self.chunk()

    # Priority table — matches lparser.c getbinopr + priority[] table.
    # Format: (left priority, right priority)
    _BINOP_PRIORITY = {
        ord('+'): (6, 6), ord('-'): (6, 6),
        ord('*'): (7, 7), ord('/'): (7, 7), ord('%'): (7, 7),
        ord('^'): (10, 9),   # right-assoc
        TK_CONCAT: (5, 4),   # right-assoc
        TK_EQ: (3, 3), TK_NE: (3, 3),
        ord('<'): (3, 3), ord('>'): (3, 3),
        TK_LE: (3, 3), TK_GE: (3, 3),
        TK_AND: (2, 2), TK_OR: (1, 1),
    }
    _UNARY_PRIORITY = 8

    def _is_unop(self, k: int) -> bool:
        return k == TK_NOT or k == ord('-')

    def _simpleexp(self):
        """simpleexp -> NUMBER | STRING | NIL | TRUE | FALSE | '...' | constructor | function | primaryexp"""
        k = self.ls.t.kind
        if k in (TK_NUMBER, TK_STRING, TK_NIL, TK_TRUE, TK_FALSE, TK_DOTS):
            self.ls.next()
            return
        if k == ord('{'):
            self._constructor()
            return
        if k == TK_FUNCTION:
            self.ls.next()
            self._funcbody()
            return
        self._primaryexp()

    def _primaryexp(self):
        """primaryexp -> NAME | '(' expr ')'; then { '.' NAME | '[' expr ']' | ':' NAME funcargs | funcargs }"""
        k = self.ls.t.kind
        if k == ord('('):
            self.ls.next()
            self.expr()
            self._check_next(ord(')'), ")")
        elif k == TK_NAME:
            self.ls.next()
        else:
            self._error("unexpected symbol")
        # suffixes
        while True:
            k = self.ls.t.kind
            if k == ord('.'):
                self.ls.next()
                self._check_next(TK_NAME, "<name>")
            elif k == ord('['):
                self.ls.next()
                self.expr()
                self._check_next(ord(']'), "]")
            elif k == ord(':'):
                self.ls.next()
                self._check_next(TK_NAME, "<name>")
                self._funcargs()
            elif k in (ord('('), TK_STRING, ord('{')):
                self._funcargs()
            else:
                return

    def _funcargs(self):
        k = self.ls.t.kind
        if k == ord('('):
            self.ls.next()
            if self.ls.t.kind != ord(')'):
                self._exprlist()
            self._check_next(ord(')'), ")")
        elif k == ord('{'):
            self._constructor()
        elif k == TK_STRING:
            self.ls.next()
        else:
            self._error("function arguments expected")

    def _exprlist(self):
        self.expr()
        while self._testnext(ord(',')):
            self.expr()

    def _constructor(self):
        """constructor -> '{' [ fieldlist ] '}'"""
        self._check_next(ord('{'), "{")
        while self.ls.t.kind != ord('}'):
            k = self.ls.t.kind
            if k == TK_NAME:
                # lookahead: 'name =' is a record field
                self.ls.lookahead()
                if self.ls.lookahead_t.kind == ord('='):
                    self.ls.next()   # name
                    self.ls.next()   # '='
                    self.expr()
                else:
                    self.expr()
            elif k == ord('['):
                self.ls.next()
                self.expr()
                self._check_next(ord(']'), "]")
                self._check_next(ord('='), "=")
                self.expr()
            else:
                self.expr()
            if not (self._testnext(ord(',')) or self._testnext(ord(';'))):
                break
        self._check_next(ord('}'), "}")

    def _subexpr(self, limit: int) -> int:
        """Operator-precedence expression parser. Returns kind of trailing binop if any."""
        if self._is_unop(self.ls.t.kind):
            self.ls.next()
            self._subexpr(self._UNARY_PRIORITY)
        else:
            self._simpleexp()
        k = self.ls.t.kind
        while k in self._BINOP_PRIORITY and self._BINOP_PRIORITY[k][0] > limit:
            right = self._BINOP_PRIORITY[k][1]
            self.ls.next()
            nxt = self._subexpr(right)
            k = nxt if nxt is not None else self.ls.t.kind
        return k

    def expr(self):
        self._subexpr(0)

    def _exprstat(self):
        """exprstat -> function call | assignment"""
        self._primaryexp()
        if self.ls.t.kind == ord('='):
            self.ls.next()
            self.expr()
        elif self.ls.t.kind == ord(','):
            # multi-assign: collect LHS, require '='
            while self._testnext(ord(',')):
                self._primaryexp()
            self._check_next(ord('='), "=")
            self._exprlist()
        # else: pure expression (function call) — already consumed

    def _ifstat(self):
        self.ls.next()                        # consume 'if'
        self.expr()
        self._check_next(TK_THEN, "then")
        self._block()
        while self.ls.t.kind == TK_ELSEIF:
            self.ls.next()
            self.expr()
            self._check_next(TK_THEN, "then")
            self._block()
        if self._testnext(TK_ELSE):
            self._block()
        self._check_next(TK_END, "end")

    def _whilestat(self):
        self.ls.next()                        # consume 'while'
        self.expr()
        self._check_next(TK_DO, "do")
        self._block()
        self._check_next(TK_END, "end")

    def _forstat(self):
        self.ls.next()                        # consume 'for'
        self._check(TK_NAME, "<name>")
        self.ls.next()
        k = self.ls.t.kind
        if k == ord('='):
            # numeric: for Name '=' exp ',' exp [',' exp] 'do' block 'end'
            self.ls.next()
            self.expr()
            self._check_next(ord(','), ",")
            self.expr()
            if self._testnext(ord(',')):
                self.expr()
        elif k == ord(',') or k == TK_IN:
            # generic: for NameList in ExpList do block end
            while self._testnext(ord(',')):
                self._check(TK_NAME, "<name>")
                self.ls.next()
            self._check_next(TK_IN, "in")
            self._exprlist()
        else:
            self._error("'=' or 'in' expected")
        self._check_next(TK_DO, "do")
        self._block()
        self._check_next(TK_END, "end")

    def _repeatstat(self):
        self.ls.next()                        # consume 'repeat'
        self._block()
        self._check_next(TK_UNTIL, "until")
        self.expr()

    def _funcstat(self):
        self.ls.next()                        # consume 'function'
        # funcname -> NAME { '.' NAME } [ ':' NAME ]
        self._check(TK_NAME, "<name>")
        self.ls.next()
        while self._testnext(ord('.')):
            self._check(TK_NAME, "<name>")
            self.ls.next()
        if self._testnext(ord(':')):
            self._check(TK_NAME, "<name>")
            self.ls.next()
        self._funcbody()

    def _funcbody(self):
        # funcbody -> '(' [parlist] ')' chunk 'end'
        self._check_next(ord('('), "(")
        if self.ls.t.kind != ord(')'):
            # parlist -> Name { ',' Name } [ ',' '...' ] | '...'
            if self.ls.t.kind == TK_DOTS:
                self.ls.next()
            else:
                self._check(TK_NAME, "<name>")
                self.ls.next()
                while self._testnext(ord(',')):
                    if self.ls.t.kind == TK_DOTS:
                        self.ls.next()
                        break
                    self._check(TK_NAME, "<name>")
                    self.ls.next()
        self._check_next(ord(')'), ")")
        self._block()
        self._check_next(TK_END, "end")

    def _localstat(self):
        self.ls.next()                        # consume 'local'
        if self._testnext(TK_FUNCTION):
            self._check(TK_NAME, "<name>")
            self.ls.next()
            self._funcbody()
            return
        # local NameList [ '=' ExpList ]
        self._check(TK_NAME, "<name>")
        self.ls.next()
        while self._testnext(ord(',')):
            self._check(TK_NAME, "<name>")
            self.ls.next()
        if self._testnext(ord('=')):
            self._exprlist()

    def _retstat(self):
        self.ls.next()                        # consume 'return'
        if not self._is_block_end() and self.ls.t.kind != ord(';'):
            self._exprlist()


def check_syntax(src: bytes, module: str) -> None:
    """Validate Lua 5.0 snippet syntax. Raises QCSyntaxError on bad input.
    No-op when ENABLE_PARSING_CHECK is False."""
    if not ENABLE_PARSING_CHECK:
        return
    lex = Lexer(io.BytesIO(src), module)
    parser = _SyntaxCheckParser(lex)
    parser.chunk()
    if parser.ls.t.kind != TK_EOS:
        raise QCSyntaxError(module, lex.linenumber, "'<eof>' expected")

# ═══════════════════════════════════════════════════════════════════════════
# Section 5: qc state machine parser
# ═══════════════════════════════════════════════════════════════════════════
#
# The heart of the tool. A state-machine parser driven by the ParseState
# enum, with one handler per state (the `_st_*` methods). It walks the
# .quest file top-to-bottom, accumulates one script per (when-name,
# state-name, arg) bucket, and leaves the collected state on `self` for
# Section 6 to emit.
#
# Three things surprise first-time readers:
#   - Or-chain fan-out: `when A or B or C: body` compiles to the same body
#     replicated under each trigger (see _st_when_body).
#   - Target rewriting: `[WHO].target ...` transforms to when_name='target'
#     with the WHO prefix pushed into when_argument (see _st_when_name).
#   - set_state / newstate / setstate silently coerce their first NAME
#     argument into a STRING literal and record it for later
#     cross-validation against defined state names (see _st_when_body).
# Each is called out in a comment at its site.

class ParseState(Enum):
    """Which phase of a .quest file the QCParser is currently in."""

    START = auto()
    QUEST = auto()
    QUEST_WITH_OR_BEGIN = auto()
    STATELIST = auto()
    STATE_NAME = auto()
    STATE_BEGIN = auto()
    WHENLIST_OR_FUNCTION = auto()
    WHEN_NAME = auto()
    WHEN_WITH_OR_BEGIN = auto()
    WHEN_BODY = auto()
    FUNCTION_NAME = auto()
    FUNCTION_ARG = auto()
    FUNCTION_BODY = auto()


@dataclass
class AScript:
    """One (when-condition, when-argument, script-body) triple for the emitter."""

    when_condition: bytes
    when_argument: bytes
    script: bytes


class QCParser:
    """State-machine parser for .quest files.

    Walks the file top-to-bottom driven by ParseState, calling the matching
    `_st_*` handler on each token. After parse() returns, the following
    attributes describe the compiled quest for Section 6 to emit:

        state_script_map[when_name][state_name] -> bytes
            simple when-clauses (no arguments).
        state_arg_script_map[when_name][state_name] -> list[AScript]
            when-clauses with arguments (target-rewritten or [idx]-style).
        start_condition: bytes            — the `with` clause on `quest`.
        all_functions: bytes              — concatenated quest-local functions.
        define_state_name_set: set[bytes] — every `state NAME` seen.
        function_defs, function_calls     — audit sets for --check-functions.
    """

    def __init__(self, lexer: "Lexer", filename: str):
        self.ls = lexer
        self.filename = filename
        self.state = ParseState.START
        self.nested = 0

        self.quest_name: bytes = b""
        self.start_condition: bytes = b""
        self.current_state_name: bytes = b""
        self.current_when_name: bytes = b""
        self.current_when_condition: bytes = b""
        self.current_when_argument: bytes = b""

        self.define_state_name_set: set = set()
        self.used_state_name_map: dict = {}
        self.state_script_map: dict = {}        # when_name → state_name → bytes
        self.state_arg_script_map: dict = {}    # when_name → state_name → [AScript]
        self.when_name_arg_vector: list = []

        self.current_function_name: bytes = b""
        self.current_function_arg: bytes = b""
        self.all_functions: bytes = b""

        self.function_defs: set = set()
        self.function_calls: set = set()

        self._quiet: bool = False
        self._out = sys.stdout

    # ─── error helpers ────────────────────────────────────────────────────
    def _error(self, msg: str):
        raise QCParseError(self.filename, self.ls.linenumber, msg)

    def _errorline(self, line: int, msg: str):
        raise QCParseError(self.filename, line, msg)

    def _say(self, line: bytes):
        if not self._quiet:
            if hasattr(self._out, "buffer"):
                self._out.buffer.write(line + b"\n")
            else:
                self._out.write(line.decode("latin-1") + "\n")

    # ─── main loop ────────────────────────────────────────────────────────
    def parse(self):
        handlers = {
            ParseState.START:                 self._st_start,
            ParseState.QUEST:                 self._st_quest,
            ParseState.QUEST_WITH_OR_BEGIN:   self._st_quest_with_or_begin,
            ParseState.STATELIST:             self._st_statelist,
            ParseState.STATE_NAME:            self._st_state_name,
            ParseState.STATE_BEGIN:           self._st_state_begin,
            ParseState.WHENLIST_OR_FUNCTION:  self._st_whenlist_or_function,
            ParseState.WHEN_NAME:             self._st_when_name,
            ParseState.WHEN_WITH_OR_BEGIN:    self._st_when_with_or_begin,
            ParseState.WHEN_BODY:             self._st_when_body,
            ParseState.FUNCTION_NAME:         self._st_function_name,
            ParseState.FUNCTION_ARG:          self._st_function_arg,
            ParseState.FUNCTION_BODY:         self._st_function_body,
        }
        while True:
            self.ls.next()
            if self.ls.t.kind == TK_EOS:
                break
            handlers[self.state]()
        assert self.nested == 0, f"unclosed block (nested={self.nested})"
        self._check_state_references()

    # ─── state handlers (top-level) ───────────────────────────────────────
    def _st_start(self):
        assert self.nested == 0
        if self.ls.t.kind == TK_QUEST:
            self.state = ParseState.QUEST
        else:
            self._error("must start with 'quest'")

    def _st_quest(self):
        assert self.nested == 0
        t = self.ls.t
        if t.kind == TK_NAME or t.kind == TK_STRING:
            self.quest_name = t.str_val
            self._say(b"QUEST : " + self.quest_name)
            self.state = ParseState.QUEST_WITH_OR_BEGIN
        else:
            self._error("quest name must be given")

    def _st_quest_with_or_begin(self):
        assert self.nested == 0
        t = self.ls.t
        if t.kind == TK_WITH:
            self.ls.next()
            parts = [format_token(self.ls.t)]
            self.ls.next()
            while self.ls.t.kind not in (TK_DO, TK_BEGIN):
                parts.append(format_token(self.ls.t))
                self.ls.next()
            self.start_condition = b" ".join(parts)
            check_syntax(b"if " + self.start_condition + b" then end", self.quest_name.decode("latin-1"))
            self._say(b"\twith " + self.start_condition)
            t = self.ls.t
        if t.kind == TK_DO or t.kind == TK_BEGIN:
            self.state = ParseState.STATELIST
            self.nested += 1
        else:
            self._error(f"quest doesn't have begin-end clause. ({format_token(t).decode('latin-1', 'replace')})")

    def _st_statelist(self):
        assert self.nested == 1
        t = self.ls.t
        if t.kind == TK_STATE:
            self.state = ParseState.STATE_NAME
        elif t.kind == TK_END:
            self.nested -= 1
            self.state = ParseState.START
        else:
            self._error("expecting 'state'")

    def _st_state_name(self):
        assert self.nested == 1
        t = self.ls.t
        if t.kind == TK_NAME or t.kind == TK_STRING:
            self.current_state_name = t.str_val
            self.define_state_name_set.add(self.current_state_name)
            self._say(b"STATE : " + self.current_state_name)
            self.state = ParseState.STATE_BEGIN
        else:
            self._error("state name must be given")

    def _st_state_begin(self):
        assert self.nested == 1
        if self.ls.t.kind in (TK_DO, TK_BEGIN):
            self.nested += 1
            self.state = ParseState.WHENLIST_OR_FUNCTION
        else:
            self._error("state doesn't have begin-end clause.")

    def _st_whenlist_or_function(self):
        assert self.nested == 2
        t = self.ls.t
        if t.kind == TK_WHEN:
            self.state = ParseState.WHEN_NAME
            self.when_name_arg_vector.clear()
        elif t.kind == TK_END:
            self.nested -= 1
            self.state = ParseState.STATELIST
        elif t.kind == TK_FUNCTION:
            self.state = ParseState.FUNCTION_NAME
        else:
            self._error("expecting 'when' or 'function'")

    def _st_when_name(self):
        """qc.cc:490-632 — parses when-name with optional .target rewrite,
        optional (args) and [idx] argument, and handles 'or' chains."""
        assert self.nested == 2
        t = self.ls.t
        if t.kind not in (TK_NAME, TK_STRING, TK_NUMBER):
            self._error("when name must be given")

        # when name base
        if t.kind == TK_NUMBER:
            self.current_when_name = format_number(t.num_val or 0.0)
            self.ls.lookahead_t = Token(ord('.'))
        else:
            self.current_when_name = t.str_val or b""
            self.ls.lookahead()

        self.current_when_argument = b""

        # optional '.second'
        if self.ls.lookahead_t.kind == ord('.'):
            self.ls.next()   # consume '.'
            self.current_when_name += b"."
            self.ls.next()   # consume second name/token
            t = self.ls.t
            second = format_token(t)
            if second == b"target":
                # Target rewrite: `[WHO].target` in .quest source transforms
                # on disk into when_name='target' with the original `WHO`
                # prefix pushed into when_argument (as `.WHO`). The emitter
                # relies on this reshape — files land under
                # target/<dotted-when>/... instead of notarget/... — so do
                # not "simplify" it back to the literal spelling.
                self.current_when_argument = b"." + self.current_when_name
                self.current_when_argument = self.current_when_argument[:-1]  # drop trailing '.'
                self.current_when_name = b"target"
            else:
                self.current_when_name += second
            self.ls.lookahead()

        # accumulate trailing .foo.bar, (args), [idx]
        arg_accum = b""
        while self.ls.lookahead_t.kind == ord('.'):
            self.ls.next()
            arg_accum += b"."
            self.ls.next()
            arg_accum += format_token(self.ls.t)
            self.ls.lookahead()

        if ENABLE_WHEN_PARENTHESIS:
            # parenthesized arg list
            if self.ls.lookahead_t.kind == ord('('):
                depth = 0
                while self.ls.lookahead_t.kind != ord(')') or depth > 1:
                    if self.ls.lookahead_t.kind == ord('('):
                        depth += 1
                    elif self.ls.lookahead_t.kind == ord(')'):
                        depth -= 1
                    self.ls.next()
                    arg_accum += format_token(self.ls.t)
                    self.ls.lookahead()
                # consume the closing ')'
                self.ls.next()
                arg_accum += b")"
                self.ls.lookahead()
            # bracketed [idx] arg
            if self.ls.lookahead_t.kind == ord('['):
                depth = 0
                while self.ls.lookahead_t.kind != ord(']') or depth > 1:
                    if self.ls.lookahead_t.kind == ord('['):
                        depth += 1
                    elif self.ls.lookahead_t.kind == ord(']'):
                        depth -= 1
                    self.ls.next()
                    arg_accum += format_token(self.ls.t)
                    self.ls.lookahead()
                # consume the closing ']'
                self.ls.next()
                arg_accum += b"]"
                self.ls.lookahead()
                # suffix .foo chain
                while self.ls.lookahead_t.kind == ord('.'):
                    self.ls.next()
                    arg_accum += b"."
                    self.ls.next()
                    arg_accum += format_token(self.ls.t)
                    self.ls.lookahead()

        self.current_when_argument += arg_accum

        # stdout message
        line = b"WHEN  : " + self.current_when_name
        if self.current_when_argument:
            line += b" (" + self.current_when_argument[1:] + b")"

        # or-chain
        if self.ls.lookahead_t.kind == TK_OR:
            self.state = ParseState.WHEN_NAME
            self.when_name_arg_vector.append((self.current_when_name, self.current_when_argument))
            self.ls.next()   # consume 'or'
            self._say(line + b" or")
        else:
            self._say(line)
            self.state = ParseState.WHEN_WITH_OR_BEGIN

    def _st_when_with_or_begin(self):
        assert self.nested == 2
        self.current_when_condition = b""
        t = self.ls.t
        if t.kind == TK_WITH:
            self.ls.next()
            parts = [format_token(self.ls.t)]
            self.ls.next()
            while self.ls.t.kind != TK_DO:
                parts.append(format_token(self.ls.t))
                self.ls.next()
            self.current_when_condition = b" ".join(parts)
            check_syntax(
                b"if " + self.current_when_condition + b" then end",
                (self.current_state_name + self.current_when_condition).decode("latin-1", "replace"),
            )
            self._say(b"\twith " + self.current_when_condition)
            t = self.ls.t
        if t.kind == TK_DO:
            self.state = ParseState.WHEN_BODY
            self.nested += 1
        else:
            self._error(f"when doesn't have begin-end clause. ({format_token(t).decode('latin-1', 'replace')})")

    def _st_when_body(self):
        """qc.cc:672-777 — accumulates tokens until nested drops to 2,
        tracks set_state/newstate/setstate string-coercion, and function calls."""
        assert self.nested == 3
        buf = bytearray()
        state_check = 0
        prev = Token(self.ls.t.kind, self.ls.t.str_val, self.ls.t.num_val)
        if prev.kind == ord('.'):
            prev.kind = TK_DO  # any non-NAME sentinel
        callname = b""
        registered = False

        while True:
            t = self.ls.t
            if t.kind in (TK_DO, TK_IF, TK_FUNCTION, TK_BEGIN):
                self.nested += 1
            elif t.kind == TK_END:
                self.nested -= 1

            if callname:
                self.ls.lookahead()
                if self.ls.lookahead_t.kind == ord('('):
                    self.function_calls.add(callname)
                    registered = True
                callname = b""
            elif t.kind == ord('('):
                if not registered and prev.kind == TK_NAME:
                    self.function_calls.add(prev.str_val or b"")
                registered = False

            if t.kind == ord('.'):
                self.ls.lookahead()
                la = self.ls.lookahead_t
                callname = (prev.str_val or format_token(prev)) + b"." + (la.str_val or format_token(la))

            # set_state / newstate / setstate NAME→STRING coercion.
            #
            # .quest authors write `set_state(waiting)` meaning the state
            # named "waiting", not a Lua variable called `waiting`. The
            # compiler silently promotes that bare NAME into a STRING
            # literal (kind = TK_STRING) so the emitted Lua uses a string,
            # which is what the server-side runtime expects.
            #
            # It also records the reference in used_state_name_map, so
            # _check_state_references can catch typos at compile time:
            # `set_state(wating)` will fail here instead of silently
            # compiling and breaking the quest on the server.
            #
            # The state_check countdown is set to 2 when we see the
            # function name (below) and fires on the first token inside
            # the call's parentheses.
            if state_check:
                state_check -= 1
                if state_check == 0:
                    if self.ls.t.kind in (TK_NAME, TK_STRING):
                        self.used_state_name_map[self.ls.linenumber] = self.ls.t.str_val or b""
                        self.ls.t.kind = TK_STRING

            if t.kind == TK_NAME and (t.str_val in (b"set_state", b"newstate", b"setstate")):
                state_check = 2

            if self.nested == 2:
                break
            buf += format_token(self.ls.t) + b" "
            prev = Token(self.ls.t.kind, self.ls.t.str_val, self.ls.t.num_val)
            self.ls.next()
            if self.ls.linenumber != self.ls.lastline:
                buf += b"\n"

        script = bytes(buf)
        check_syntax(script, (self.current_state_name + self.current_when_condition).decode("latin-1", "replace"))

        # Or-chain fan-out.
        #
        # .quest syntax allows `when A or B or C: body`, which compiles to
        # the same body replicated under each of A, B, C. _st_when_name
        # collected the (name, arg) tuples into when_name_arg_vector as it
        # saw each `or`; now we walk that list and append this script to
        # every (when, state) bucket it mentions. Reversing first preserves
        # source order in the output.
        self.when_name_arg_vector.reverse()
        while True:
            if not self.current_when_argument:
                if not self.current_when_condition:
                    self.state_script_map.setdefault(self.current_when_name, {}).setdefault(self.current_state_name, b"")
                    self.state_script_map[self.current_when_name][self.current_state_name] += script
                else:
                    wrapped = b"if " + self.current_when_condition + b" then " + script + b" return end "
                    self.state_script_map.setdefault(self.current_when_name, {}).setdefault(self.current_state_name, b"")
                    self.state_script_map[self.current_when_name][self.current_state_name] += wrapped
            else:
                self.state_arg_script_map.setdefault(self.current_when_name, {}).setdefault(self.current_state_name, []).append(
                    AScript(self.current_when_condition, self.current_when_argument, script)
                )
            if self.when_name_arg_vector:
                self.current_when_name, self.current_when_argument = self.when_name_arg_vector.pop()
            else:
                break

        self.state = ParseState.WHENLIST_OR_FUNCTION
    def _st_function_name(self):
        t = self.ls.t
        if t.kind == TK_NAME:
            self.current_function_name = t.str_val or b""
            self.function_defs.add(self.quest_name + b"." + self.current_function_name)
            self.state = ParseState.FUNCTION_ARG

    def _st_function_arg(self):
        if self.ls.t.kind != ord('('):
            self._error("function arg list must start with '('")
        self.ls.next()
        self.current_function_arg = b"("
        if self.ls.t.kind != ord(')'):
            while True:
                if self.ls.t.kind == TK_NAME:
                    self.current_function_arg += self.ls.t.str_val or b""
                    self.ls.next()
                    if self.ls.t.kind != ord(')'):
                        self.current_function_arg += b","
                else:
                    self._error(f"invalid argument name for function {self.current_function_name.decode('latin-1','replace')}")
                if self.ls.t.kind == ord(','):
                    self.ls.next()
                    continue
                break
        self.current_function_arg += b")"
        self.state = ParseState.FUNCTION_BODY
        self.nested += 1

    def _st_function_body(self):
        """qc.cc:816-881 — similar accumulation to when-body, plus all_functions append."""
        assert self.nested == 3
        buf = bytearray()
        prev = Token(self.ls.t.kind, self.ls.t.str_val, self.ls.t.num_val)
        if prev.kind == ord('.'):
            prev.kind = TK_DO
        callname = b""
        registered = False

        while self.nested >= 3:
            t = self.ls.t
            if t.kind in (TK_DO, TK_IF, TK_FUNCTION, TK_BEGIN):
                self.nested += 1
            elif t.kind == TK_END:
                self.nested -= 1

            if callname:
                self.ls.lookahead()
                if self.ls.lookahead_t.kind == ord('('):
                    self.function_calls.add(callname)
                    registered = True
                callname = b""
            elif t.kind == ord('('):
                if not registered and prev.kind == TK_NAME:
                    self.function_calls.add(prev.str_val or b"")
                registered = False

            if t.kind == ord('.'):
                self.ls.lookahead()
                la = self.ls.lookahead_t
                callname = (prev.str_val or format_token(prev)) + b"." + (la.str_val or format_token(la))

            buf += format_token(self.ls.t) + b" "
            if self.nested == 2:
                break
            prev = Token(self.ls.t.kind, self.ls.t.str_val, self.ls.t.num_val)
            self.ls.next()
            if self.ls.linenumber != self.ls.lastline:
                buf += b"\n"

        self.state = ParseState.WHENLIST_OR_FUNCTION
        # Format matches qc.cc:874-878: ",name= function (args)body"
        self.all_functions += (
            b"," + self.current_function_name
            + b"= function " + self.current_function_arg + bytes(buf)
        )
        self._say(b"FUNCTION " + self.current_function_name + self.current_function_arg)

    def _check_state_references(self):
        for line, name in self.used_state_name_map.items():
            if name not in self.define_state_name_set:
                self._errorline(line, f"state name not found : {name.decode('latin-1', 'replace')}")

# ═══════════════════════════════════════════════════════════════════════════
# Section 6: Emitter
# ═══════════════════════════════════════════════════════════════════════════
#
# Writes four kinds of files under output_dir (default: object/):
#   - state/<quest>           — the state-id table (CRC32 of each state name).
#   - begin_condition/<quest> — the `with` expression attached to `quest`.
#   - notarget/<when>/<quest>.<state>           — simple when-clauses.
#   - <target>/<when>/<quest>.<state>.<N>.*     — when-clauses with args.
# All written with CRLF line endings to match qc.exe's Windows-era output.
#
# The signed-CRC quirk in _emit_state_file exists because qc.cc stores each
# CRC in a C++ `int` (signed) and cout prints it as signed decimal. Matching
# that is a byte-equivalence requirement, not a display preference.

def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content.replace(b"\n", b"\r\n"))


def emit(parser: "QCParser", output_dir: Path) -> None:
    """Write the compiled quest to output_dir.

    Produces up to four kinds of files (see Section 6 intro). The parser
    must have already been driven to completion via parser.parse().
    """
    output_dir.mkdir(mode=0o700, exist_ok=True)
    if parser.define_state_name_set:
        _emit_state_file(parser, output_dir)
    if parser.start_condition:
        _emit_begin_condition(parser, output_dir)
    _emit_when_arg_scripts(parser, output_dir)
    _emit_when_simple_scripts(parser, output_dir)


def _emit_state_file(p: "QCParser", out: Path) -> None:
    path = out / "state" / p.quest_name.decode("latin-1")
    buf = bytearray()
    buf += p.quest_name + b'={["start"]=0'
    crcs = {b"start": 0}
    seen = {0}
    for name in sorted(p.define_state_name_set):
        if name == b"start":
            continue
        crc = crc32(name)
        if crc in seen:
            sys.stdout.write("WARN: state CRC conflict occur! state index may differ in next compile time.\n")
            while crc in seen:
                crc = (crc + 1) & 0xFFFFFFFF
        seen.add(crc)
        crcs[name] = crc
    for name in sorted(p.define_state_name_set):
        if name != b"start":
            # qc.cc:914 stores each CRC in a C++ `int` (signed) and prints
            # it via cout, which emits signed decimal. Any CRC with bit 31
            # set therefore appears as a negative number on disk. We match
            # that exactly — it is a byte-equivalence requirement, not a
            # display choice. Changing it would break every server that
            # cached state IDs from a previous compile.
            c = crcs[name]
            signed = c - 0x100000000 if c >= 0x80000000 else c
            buf += b',["' + name + b'"]=' + str(signed).encode("ascii")
    buf += p.all_functions + b'}'
    _write_bytes(path, bytes(buf))


def _emit_begin_condition(p: "QCParser", out: Path) -> None:
    path = out / "begin_condition" / p.quest_name.decode("latin-1")
    _write_bytes(path, b"return " + p.start_condition)


def _emit_when_arg_scripts(p: "QCParser", out: Path) -> None:
    for when_name, state_map in sorted(p.state_arg_script_map.items()):
        if b"." not in when_name:
            low = when_name.lower()
            base = out / "notarget" / low.decode("latin-1")
        else:
            # Target portion preserves case; rest lowercased. qc.cc:985-993.
            idx = when_name.find(b".")
            target_part = when_name[:idx]              # case-preserved
            rest_part = when_name[idx+1:].lower()      # lowercased
            base = out / target_part.decode("latin-1") / rest_part.decode("latin-1")
        for state_name, scripts in sorted(state_map.items()):
            for i, s in enumerate(scripts):
                stem = p.quest_name + b"." + state_name + b"." + str(i).encode("ascii") + b"."
                _write_bytes(base / (stem + b"script").decode("latin-1"), s.script)
                if s.when_condition:
                    _write_bytes(base / (stem + b"when").decode("latin-1"), b"return " + s.when_condition)
                else:
                    _write_bytes(base / (stem + b"when").decode("latin-1"), b"")
                _write_bytes(base / (stem + b"arg").decode("latin-1"), s.when_argument[1:] if s.when_argument else b"")


def _emit_when_simple_scripts(p: "QCParser", out: Path) -> None:
    for when_name, state_map in sorted(p.state_script_map.items()):
        if b"." not in when_name:
            low = when_name.lower()
            base = out / "notarget" / low.decode("latin-1")
        else:
            idx = when_name.find(b".")
            target_part = when_name[:idx]
            rest_part = when_name[idx+1:].lower()
            base = out / target_part.decode("latin-1") / rest_part.decode("latin-1")
        for state_name, script in sorted(state_map.items()):
            path = base / (p.quest_name + b"." + state_name).decode("latin-1")
            _write_bytes(path, script)

# ═══════════════════════════════════════════════════════════════════════════
# Section 7: CLI + main
# ═══════════════════════════════════════════════════════════════════════════
#
# The library-shaped entry point is `compile_one(quest_path, output_dir, ...)`.
# `main()` is thin CLI plumbing around it. Exit codes: 0 on success, 1 on
# any QCError, 130 on Ctrl+C.

def _check_functions_file(parser: QCParser, quest_functions_path: Path) -> None:
    known: set = set()
    if quest_functions_path.exists():
        for line in quest_functions_path.read_bytes().split(b"\n"):
            line = line.strip()
            if line:
                known.add(line)
    known |= parser.function_defs
    undeclared = sorted(parser.function_calls - known)
    if undeclared:
        sys.stdout.write("Calls undeclared function! :\n")
        for name in undeclared:
            sys.stdout.write(name.decode("latin-1", "replace") + "\n")


def compile_one(quest_path: Path, output_dir: Path, quiet: bool, do_fn_check: bool) -> None:
    """Compile one .quest file end-to-end.

    Reads quest_path, runs Lexer → QCParser → emit, writes files under
    output_dir. If quiet is False, prints QUEST: / STATE: / WHEN: status
    lines to stdout. If do_fn_check is True, warns about function calls
    not declared in ./quest_functions.
    """
    with open(quest_path, "rb") as f:
        lexer = Lexer(f, str(quest_path))
        parser = QCParser(lexer, str(quest_path))
        parser._quiet = quiet
        parser.parse()
    emit(parser, output_dir)
    if do_fn_check:
        _check_functions_file(parser, Path("quest_functions"))


def _parse_args(argv):
    ap = argparse.ArgumentParser(prog="qc",
        description="Metin2 quest compiler (Python port).")
    ap.add_argument("files", nargs="+", metavar="FILE", help=".quest source files")
    ap.add_argument("-o", "--output-dir", default="object")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check-functions", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--version", action="version",
                    version=f"qc.py {__version__}")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    """CLI entry point. Return the process exit code (0/1/130)."""
    args = _parse_args(argv)
    out = Path(args.output_dir)
    for f in args.files:
        try:
            compile_one(Path(f), out, args.quiet, args.check_functions)
        except QCError as e:
            sys.stderr.write(str(e) + "\n")
            if args.verbose:
                traceback.print_exc()
            return 1
        except KeyboardInterrupt:
            return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
