import os
import hashlib
import datetime

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def generate_inventory(root_dir, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"Inventory generated at {datetime.datetime.now()}\n")
        out.write(f"Root: {root_dir}\n")
        out.write("-" * 80 + "\n")
        out.write(f"{'Path':<60} | {'Size (Bytes)':<12} | {'SHA256'}\n")
        out.write("-" * 80 + "\n")

        for root, dirs, files in os.walk(root_dir):
            # Skip virtual environments and node_modules to keep it readable
            if ".venv" in dirs:
                dirs.remove(".venv")
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if ".git" in dirs:
                dirs.remove(".git")
            
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    file_hash = calculate_sha256(filepath)
                    rel_path = os.path.relpath(filepath, root_dir)
                    out.write(f"{rel_path:<60} | {size:<12} | {file_hash}\n")
                except Exception as e:
                    out.write(f"{filepath} - Error accessing file: {e}\n")

if __name__ == "__main__":
    generate_inventory(".", "project_inventory.txt")
    print("Inventory generated in project_inventory.txt")
