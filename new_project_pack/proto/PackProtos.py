import os
import shutil
import subprocess

folders = ["tr", "de", "dk", "en", "es", "fr", "hu", "it", "nl", "pl", "pt", "ro", "cz"]

source_path = r'.'
destination_base_path = r'_out'

proto_txt_files = ['item_proto.txt', 'mob_proto.txt']
required_lang_files = ['item_names.txt', 'mob_names.txt']

out_file_names = ['item_proto', 'mob_proto']

for folder in folders:
    translate_folder = os.path.join(source_path, folder)
    os.makedirs(translate_folder, exist_ok=True)

    print("")
    print(f"Packing language: {folder}")

    # Dil klasorundeki item_names / mob_names kontrolu
    for required_file in required_lang_files:
        required_path = os.path.join(translate_folder, required_file)

        if not os.path.exists(required_path):
            print(f"Eksik dil dosyasi: {required_path}")

    # Ana klasorden item_proto.txt ve mob_proto.txt kopyala
    for file_name in proto_txt_files:
        source_file_path = os.path.join(source_path, file_name)
        destination_file_path = os.path.join(translate_folder, file_name)

        if not os.path.exists(source_file_path):
            print(f"Eksik proto dosyasi: {source_file_path}")
            continue

        shutil.copyfile(source_file_path, destination_file_path)
        print(f"Copied {file_name} to {translate_folder}")

    # DumpProto calistir
    command = "..\\dumpproto.exe -pmi"
    result = subprocess.run(command, shell=True, cwd=translate_folder)

    if result.returncode != 0:
        print(f"DumpProto hata verdi: {translate_folder}")
        continue

    print(f"Ran DumpProto in {translate_folder}")

    # Cikti klasoru olustur
    destination_folder = os.path.join(destination_base_path, folder)
    os.makedirs(destination_folder, exist_ok=True)

    # item_proto ve mob_proto dosyalarini _out/dil icine tasi
    for file_name in out_file_names:
        translate_file_path = os.path.join(translate_folder, file_name)
        destination_file_path = os.path.join(destination_folder, file_name)

        if not os.path.exists(translate_file_path):
            print(f"Cikti dosyasi bulunamadi: {translate_file_path}")
            continue

        if os.path.exists(destination_file_path):
            os.remove(destination_file_path)

        shutil.move(translate_file_path, destination_file_path)
        print(f"Moved {file_name} to {destination_folder}")

    # Gecici kopyalanan proto txt dosyalarini temizle
    for file_name in proto_txt_files:
        temp_file_path = os.path.join(translate_folder, file_name)

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)