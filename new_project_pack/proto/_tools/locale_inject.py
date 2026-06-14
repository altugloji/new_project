#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import re
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Script tools klasorundeyse, ana klasoru bulur.
ROOT = Path(__file__).resolve().parent.parent


# python _tools/locale_inject.py --file item_names.txt --input _tools/_input.txt
# python _tools/locale_inject.py --file mob_names.txt --input _tools/_input.txt

LOCALE_ROOT = ROOT

LANG_ENCODINGS = {
    "tr": "cp1254",
    "pl": "cp1250",
    "cz": "cp1250",
    "hu": "cp1250",
    "ro": "cp1250",
    "de": "cp1252",
    "en": "cp1252",
    "fr": "cp1252",
    "es": "cp1252",
    "it": "cp1252",
    "pt": "cp1252",
    "nl": "cp1252",
    "dk": "cp1252",
}

ALLOWED_FILES = (
    "item_names.txt",
    "mob_names.txt",
)

ENCODING_FALLBACKS = {
    "cp1250": {
        "\u0218": "\u015E",
        "\u0219": "\u015F",
        "\u021A": "\u0162",
        "\u021B": "\u0163",
    },
}

COMMON_FALLBACKS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201C": '"',
    "\u201D": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00A0": " ",
}


def parse_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for raw_line in text.splitlines():
        m = re.match(r"^\s*\[([A-Za-z]{2})\]\s*$", raw_line)

        if m:
            if current is not None:
                blocks[current] = strip_block("\n".join(buf))

            current = m.group(1).lower()
            buf = []
            continue

        if current is None:
            continue

        buf.append(raw_line)

    if current is not None:
        blocks[current] = strip_block("\n".join(buf))

    return {k: v for k, v in blocks.items() if v.strip()}


def strip_block(s: str) -> str:
    lines = s.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)


def smart_read(path: Path, lang: str) -> tuple[str, str, str]:
    raw = path.read_bytes()

    if raw[:3] == b"\xef\xbb\xbf":
        text = raw[3:].decode("utf-8")
        enc = "utf-8-sig"
    else:
        text = None
        enc = None

        try:
            text = raw.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            pass

        if text is None:
            for cand in (LANG_ENCODINGS.get(lang), "cp1252", "latin-1"):
                if not cand:
                    continue

                try:
                    text = raw.decode(cand)
                    enc = cand
                    break
                except UnicodeDecodeError:
                    continue

        if text is None or enc is None:
            raise UnicodeDecodeError("auto", raw, 0, 1, f"{path} okunamadi")

    if "\r\n" in text:
        nl = "\r\n"
    elif "\r" in text:
        nl = "\r"
    else:
        nl = "\n"

    return text, enc, nl


def normalize_block(block: str, newline: str) -> str:
    lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return newline.join(lines) + newline


def first_tab_key(line: str) -> str | None:
    if not line.strip():
        return None

    key = line.split("\t", 1)[0].strip()
    return key if key else None


def merge_lines(existing: str, incoming_block: str, nl: str) -> tuple[str, int, int]:
    lines = existing.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    if lines and lines[-1] == "":
        lines.pop()

    key_to_index: dict[str, int] = {}

    for i, raw in enumerate(lines):
        k = first_tab_key(raw)

        if k is not None:
            key_to_index[k] = i

    incoming = incoming_block.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    if incoming and incoming[-1] == "":
        incoming.pop()

    replaced = 0
    appended = 0

    for raw in incoming:
        if not raw.strip():
            continue

        k = first_tab_key(raw)

        if k is not None and k in key_to_index:
            lines[key_to_index[k]] = raw
            replaced += 1
        else:
            if k is not None:
                key_to_index[k] = len(lines)

            lines.append(raw)
            appended += 1

    out = nl.join(lines)

    if out:
        out += nl

    return out, replaced, appended


def encode_with_fallbacks(text: str, enc: str) -> tuple[bytes, str, list[str]]:
    replaced: list[str] = []

    def apply_table(s: str, table: dict[str, str]) -> str:
        nonlocal replaced

        for src, dst in table.items():
            if src in s:
                replaced.append(f"{src!r}->{dst!r}")
                s = s.replace(src, dst)

        return s

    s = apply_table(text, COMMON_FALLBACKS)
    s = apply_table(s, ENCODING_FALLBACKS.get(enc, {}))

    try:
        return s.encode(enc), enc, replaced
    except UnicodeEncodeError as e:
        bad = e.object[e.start:e.end]
        print(f"[!] '{enc}' icinde olmayan karakter: {bad!r}")
        return s.encode("utf-8"), "utf-8", replaced


def inject(target_file: str, lang: str, content: str, dry_run: bool) -> bool:
    folder = LOCALE_ROOT / lang
    path = folder / target_file

    if not path.is_file():
        print(f"[!] {lang}: {path} bulunamadi, atlandi.")
        return False

    text, enc, nl = smart_read(path, lang)
    block_text = normalize_block(content, nl)
    new_text, n_rep, n_app = merge_lines(text, block_text, nl)

    if dry_run:
        print(
            f"[DRY] {lang}: {path} "
            f"(encoding={enc}, newline={nl!r}, updated={n_rep}, added={n_app})"
        )
        return True

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)

    encoded, enc_used, replaced = encode_with_fallbacks(new_text, enc)

    if replaced:
        sample = ", ".join(sorted(replaced))
        print(f"[i] {lang}: karakter donusumu uygulandi: {sample}")

    if enc_used != enc:
        print(f"[!] {lang}: encoding {enc} yerine {enc_used} kullanildi.")

    path.write_bytes(encoded)

    print(
        f"[OK] {lang}: {path} "
        f"(encoding={enc_used}, updated={n_rep}, added={n_app}, backup={backup.name})"
    )

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Coklu dil item_names/mob_names/locale dosyalarina toplu satir ekler veya gunceller."
    )

    parser.add_argument("--file", required=True, choices=ALLOWED_FILES, help="Hedef dosya adi")
    parser.add_argument("--input", help="Girdi dosyasi. Verilmezse stdin kullanilir.")
    parser.add_argument("--dry-run", action="store_true", help="Dosyalari degistirme, sadece kontrol et.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Uyumluluk icin vardir, yok sayilir. Guncelleme her zaman ilk TAB alanina goredir.",
    )

    args = parser.parse_args()

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    blocks = parse_blocks(text)

    if not blocks:
        print("Girdi icinde [TR], [EN], [DE] gibi dil blogu bulunamadi.")
        sys.exit(1)

    print(f"Hedef: {args.file}")
    print(f"Kok klasor: {LOCALE_ROOT}")
    print(f"Dil sayisi: {len(blocks)}")
    print("Mod: ilk TAB oncesi ayniysa guncelle, yoksa sona ekle")

    if args.dry_run:
        print("DRY-RUN aktif, dosyalar degismeyecek.")

    ok = 0

    for lang, content in sorted(blocks.items()):
        if inject(args.file, lang, content, args.dry_run):
            ok += 1

    print(f"\nBitti. Basarili: {ok}/{len(blocks)}")


if __name__ == "__main__":
    main()