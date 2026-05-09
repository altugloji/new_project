#!/usr/bin/env python3
"""locale_inject.py

Çoklu dil locale dosyalarına ([TR], [PL] ... blokları halinde) toplu satır enjekte eder.

Kullanım:
    python tools/locale_inject.py --file locale_game.txt --input tools/_input.txt
    python tools/locale_inject.py --file locale_interface.txt --input tools/_input.txt
    python tools/locale_inject.py --file locale_string.txt --input tools/_input.txt --append   # sona ekler
    python tools/locale_inject.py --file locale_interface.txt --input tools/_input.txt --dry-run
    python tools/locale_inject.py --file locale_quest.txt --input tools/_input.txt
    python tools/locale_inject.py --file itemdesc.txt --input tools/_input.txt

Girdi dosyası örneği (UTF-8 olarak kaydet):

    [TR]
    2101    <Demirci> %s isimli oyuncu %s elde etti!
    2102    <Demirci> %s isimli oyuncu %s yaktı!

    [PL]
    2101    <Kowal> Gracz %s zdobyl %s!
    2102    <Kowal> Gracz %s spalil %s!

Davranış:
- Her [XX] bloğu locale/locale/<xx>/<dosya>  başına eklenir (varsayılan).
- --append verilirse en sona eklenir.
- Mevcut dosyanın encoding'ini ve satır sonlarını korur.
- Otomatik yedek (.bak) bırakır.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import re
from pathlib import Path

# Windows konsolu cp1254/cp850 olabiliyor; tüm Unicode karakterleri sorunsuz
# yazdırabilmek için stdout/stderr'i UTF-8'e ayarla.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# Proje köküne göre locale klasörü
ROOT = Path(__file__).resolve().parent.parent
LOCALE_ROOT = ROOT / "locale" / "locale"

# Dile göre tipik Windows codepage'leri (UTF-8 olmayan dosyalar için fallback)
LANG_ENCODINGS = {
    "tr": "cp1254",  # Latin-5
    "pl": "cp1250",  # Orta Avrupa
    "cz": "cp1250",
    "hu": "cp1250",
    "ro": "cp1250",
    "de": "cp1252",  # Batı Avrupa
    "en": "cp1252",
    "fr": "cp1252",
    "es": "cp1252",
    "it": "cp1252",
    "pt": "cp1252",
    "nl": "cp1252",
    "dk": "cp1252",
}

ALLOWED_FILES = (
    "locale_game.txt",
    "locale_interface.txt",
    "locale_string.txt",
    "locale_quest.txt",
    "itemdesc.txt",
)

# Bazı Unicode karakterler hedef codepage'de yer almaz. Kayıpsız (ya da
# Metin2 locale geleneğine uygun) eşdeğerleri varsa burada çevirilir.
# Örn. Romence "virgüllü" harfler cp1250'de yok; "çengelli" eşdeğerlerine
# çevrilir (Metin2 RO locale dosyaları bu karakterleri zaten böyle kullanır).
ENCODING_FALLBACKS = {
    "cp1250": {
        "\u0218": "\u015E",  # Ș -> Ş
        "\u0219": "\u015F",  # ș -> ş
        "\u021A": "\u0162",  # Ț -> Ţ
        "\u021B": "\u0163",  # ț -> ţ
    },
}

# Tüm encoding'ler için ortak güvenli çevrimler (akıllı tırnaklar vb.)
COMMON_FALLBACKS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201C": '"',
    "\u201D": '"',
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2026": "...",
    "\u00A0": " ",  # non-breaking space
}


def parse_blocks(text: str) -> dict[str, str]:
    """`[XX]` başlıklı blokları sözlüğe ayırır. Anahtarlar küçük harfli dil kodu."""
    blocks: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for raw_line in text.splitlines():
        m = re.match(r"^\s*\[([A-Za-z]{2})\]\s*$", raw_line)
        if m:
            if current is not None:
                blocks[current] = _strip_block("\n".join(buf))
            current = m.group(1).lower()
            buf = []
            continue
        if current is None:
            # Henüz blok başlamadıysa boş satırları yutarız.
            continue
        buf.append(raw_line)

    if current is not None:
        blocks[current] = _strip_block("\n".join(buf))

    # Boş blokları at
    return {k: v for k, v in blocks.items() if v.strip()}


def _strip_block(s: str) -> str:
    """Blok içindeki başta/sonda boş satırları temizler, son satıra \\n koyar."""
    lines = s.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def smart_read(path: Path, lang: str) -> tuple[str, str, str]:
    """Dosyayı uygun encoding'le okur. (text, encoding, newline) döndürür."""
    raw = path.read_bytes()

    # BOM
    if raw[:3] == b"\xef\xbb\xbf":
        text = raw[3:].decode("utf-8")
        enc = "utf-8-sig"
    else:
        text = None
        enc = None
        # Önce UTF-8 dene
        try:
            text = raw.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            pass
        # Sonra dile özel codepage, ardından cp1252
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
        if text is None:
            raise UnicodeDecodeError("auto", raw, 0, 1, f"{path} okunamadı")

    # Satır sonu tespiti
    if "\r\n" in text:
        nl = "\r\n"
    elif "\r" in text:
        nl = "\r"
    else:
        nl = "\n"
    return text, enc, nl


def normalize_block(block: str, newline: str) -> str:
    """Blok içeriğini hedef dosyanın newline'ına çevirir, sonuna newline ekler."""
    lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return newline.join(lines) + newline


def inject(target_file: str, lang: str, content: str, *, append: bool, dry_run: bool) -> bool:
    folder = LOCALE_ROOT / lang
    path = folder / target_file
    if not path.is_file():
        print(f"[!] {lang}: {path} bulunamadı, atlanıyor.")
        return False

    text, enc, nl = smart_read(path, lang)
    block_text = normalize_block(content, nl)

    if append:
        # Dosya newline ile bitmiyorsa önce bir tane ekle
        if text and not text.endswith(nl):
            text = text + nl
        new_text = text + block_text
    else:
        new_text = block_text + text

    if dry_run:
        print(f"[DRY] {lang}: {path}  (encoding={enc}, newline={nl!r}, +{block_text.count(nl)} satır)")
        return True

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)

    encoded, enc_used, replaced = encode_with_fallbacks(new_text, enc)

    if replaced:
        sample = ", ".join(sorted(replaced))
        print(f"[i] {lang}: '{enc}' uyumu için karakter dönüşümü uygulandı: {sample}")

    if enc_used != enc:
        print(
            f"[!] {lang}: '{enc}' ile encode edilemedi, '{enc_used}' kullanıldı "
            f"(dosya encoding'i değişti)."
        )

    path.write_bytes(encoded)
    print(f"[OK] {lang}: {path}  (encoding={enc_used}, newline={nl!r}, yedek={backup.name})")
    return True


def encode_with_fallbacks(text: str, enc: str) -> tuple[bytes, str, list[str]]:
    """Metni hedef encoding'e çevirir; karakter eşlemesi gerekirse uygular.

    Dönüş: (bytes, gerçekten kullanılan encoding, dönüştürülen karakterlerin listesi).
    """
    replaced: list[str] = []

    def apply_table(s: str, table: dict[str, str]) -> str:
        nonlocal replaced
        if not table:
            return s
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
        # Hangi karakter sorun çıkardı, raporla.
        bad = e.object[e.start:e.end]
        print(f"[!] '{enc}' kapsamında olmayan karakter: {bad!r}")
        return s.encode("utf-8"), "utf-8", replaced


def main():
    p = argparse.ArgumentParser(description="locale_*.txt dosyalarına dil bloklarını enjekte eder.")
    p.add_argument("--file", required=True, choices=ALLOWED_FILES, help="Hedef dosya adı")
    p.add_argument("--input", help="Girdi metin dosyası (UTF-8). Verilmezse stdin'den okur.")
    p.add_argument("--append", action="store_true", help="Başa değil sona ekle")
    p.add_argument("--dry-run", action="store_true", help="Yazma, sadece ne yapacağını göster")
    args = p.parse_args()

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    blocks = parse_blocks(text)
    if not blocks:
        print("Girdi içinde [XX] bloğu bulunamadı. Örnek için tools/_input.txt dosyasına bak.")
        sys.exit(1)

    print(f"Hedef: {args.file}  Dil sayısı: {len(blocks)}  Mod: {'append' if args.append else 'prepend'}")
    if args.dry_run:
        print("DRY-RUN aktif (dosyalar değişmeyecek).\n")

    ok = 0
    for lang, content in sorted(blocks.items()):
        if inject(args.file, lang, content, append=args.append, dry_run=args.dry_run):
            ok += 1

    print(f"\nBitti. Başarılı: {ok}/{len(blocks)}")


if __name__ == "__main__":
    main()
