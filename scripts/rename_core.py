import os

ROOT_DIR = "/Users/apple/Downloads/offshore/backend"

for root, _, files in os.walk(ROOT_DIR):
    if "node_modules" in root or ".venv" in root or "venv" in root or ".git" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    content = f.read()
                except UnicodeDecodeError:
                    continue
            
            new_content = content.replace("app.core.", "app.config.")
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

print("Core renamed to config in backend imports.")
