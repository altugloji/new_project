# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path.cwd()

BAT_FILE = Path(r"C:\Windows\Sysnative\PackMakerLite_p.bat")
if not BAT_FILE.exists():
    BAT_FILE = Path(r"C:\Windows\System32\PackMakerLite_p.bat")

OUTPUT_DIR = (BASE_DIR / "../client/pack").resolve()

IGNORE_FOLDERS = {
    ".git",
    "__pycache__",
}

GREEN = "\033[92m"
RESET = "\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def list_folders():
    return [
        p for p in BASE_DIR.iterdir()
        if p.is_dir() and p.name not in IGNORE_FOLDERS
    ]


def show_folders():
    folders = list_folders()

    print("Mevcut klasörler:\n")
    for folder in folders:
        print(f"- {folder.name}")

    print("\n'all' yazarsan tüm klasörler paketlenir.")
    print("'exit' yazarsan program kapanır.")

    return folders


def move_pack_outputs(folder_name):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    possible_files = [
        BASE_DIR / f"{folder_name}.edata",
        BASE_DIR / f"{folder_name}.epk",
    ]

    moved = []

    for file_path in possible_files:
        if file_path.exists():
            target = OUTPUT_DIR / file_path.name

            if target.exists():
                target.unlink()

            shutil.move(str(file_path), str(target))
            moved.append(target.name)

    if moved:
        return f"{GREEN}[OK]{RESET} {folder_name} çıktıları taşındı: {', '.join(moved)}"

    return f"[UYARI] {folder_name} için taşınacak çıktı bulunamadı."


def pack_folder(folder_path):
    if not BAT_FILE.exists():
        return f"[HATA] PackMakerLite_p.bat bulunamadı: {BAT_FILE}"

    print(f"\n[PACK] {folder_path.name} paketleniyor...")

    try:
        subprocess.run(
            f'"{BAT_FILE}" "{folder_path}" nopause',
            cwd=str(BASE_DIR),
            shell=True,
            check=True
        )

        return move_pack_outputs(folder_path.name)

    except subprocess.CalledProcessError as e:
        return f"[HATA] {folder_path.name} paketlenirken hata oluştu.\n{e}"


def main():
    os.system("")
    last_message = ""

    while True:
        clear_screen()

        folders = show_folders()

        if last_message:
            print("\n" + "-" * 50)
            print(last_message)
            print("-" * 50)

        if not folders:
            print("[HATA] Bu dizinde paketlenecek klasör yok.")
            input("\nÇıkmak için Enter'a bas...")
            break

        choice = input("\nHangi klasörü kapatmak istiyorsun?: ").strip()

        if not choice:
            last_message = "[HATA] Klasör adı boş olamaz."
            continue

        if choice.lower() in ("exit", "quit", "q"):
            print("[ÇIKIŞ] Program kapatıldı.")
            break

        if choice.lower() == "all":
            results = []

            for folder in folders:
                result = pack_folder(folder)
                results.append(result)

            last_message = "\n".join(results)
            continue

        selected = BASE_DIR / choice

        if not selected.exists() or not selected.is_dir():
            last_message = f"[HATA] Böyle bir klasör bulunamadı: {choice}"
            continue

        result = pack_folder(selected)
        last_message = result


if __name__ == "__main__":
    main()