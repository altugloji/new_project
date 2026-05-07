# martysama0134' script for sanatizing data/monster .msa files
import os

def process_msa_file(file_path):
    """Processes a single .msa file (loading as bytes):
    - Converts backslashes to forward slashes
    - Ensures the file ends with a newline character (\n)
    - Performs additional replacements as specified
    """

    contents = ""
    with open(file_path, "rb") as file:
        contents = file.read().replace(b"\\", b"/")  # Replace using bytes
        contents = contents.replace(b"Ymir Work", b"ymir work")
        contents = contents.replace(b"YMIR WORK", b"ymir work")
        contents = contents.replace(b"D:", b"d:")
        contents = contents.replace(b'.GR2"', b'.gr2"')
        contents = contents.replace(b"Accumulation   0", b"Accumulation     0")  # Adjusted spacing
        contents = contents.replace(b"\r", b"") # Remove carriage return
        if not contents.endswith(b"\n"):  # Add trailing nl if missing
            contents += b"\n"

    with open(file_path, "wb") as file:
        file.write(contents)


def process_subfolders(root_dir):
    """Recursively processes .msa files in subfolders."""

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".msa"):
                file_path = os.path.join(root, file)
                process_msa_file(file_path)


if __name__ == "__main__":
    root_dir = "."  # Replace with the actual path
    process_subfolders(root_dir)
