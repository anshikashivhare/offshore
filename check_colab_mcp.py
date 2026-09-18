import json
import os
import shutil
from pathlib import Path

print("=" * 55)
print(" GOOGLE COLAB MCP — LOCAL DIAGNOSTIC")
print("=" * 55)

# 1. Check common MCP configuration locations
home = Path.home()

config_paths = [
    home / ".gemini" / "antigravity" / "mcp_config.json",
    home / ".config" / "Antigravity" / "mcp_config.json",
    home / ".gemini" / "settings.json",
    Path.cwd() / ".antigravity" / "mcp_config.json",
    home / ".gemini" / "config" / "mcp_config.json"
]

print("\n[1] MCP configuration files")

found_configs = []

for path in config_paths:
    if path.exists():
        print(f"FOUND: {path}")
        found_configs.append(path)
    else:
        print(f"Not found: {path}")

# 2. Inspect discovered configurations
print("\n[2] Searching configurations for Colab")

colab_found = False

for path in found_configs:
    try:
        with path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})

        if not isinstance(servers, dict):
            print(f"Unexpected MCP configuration format: {path}")
            continue

        for name, settings in servers.items():
            if "colab" in name.lower() or "colab" in str(settings).lower():
                colab_found = True
                print(f"\nColab-related entry found in: {path}")
                print("Server name:", name)

                if isinstance(settings, dict):
                    print("Command:", settings.get("command"))
                    print("Arguments:", settings.get("args"))
                    print("Environment variables configured:",
                          bool(settings.get("env")))

    except json.JSONDecodeError:
        print(f"Invalid JSON: {path}")
    except Exception as e:
        print(f"Could not inspect {path}: {e}")

if not colab_found:
    print("No Colab-related entry found in inspected configs.")

# 3. Check common local dependencies
print("\n[3] Local executable checks")

for executable in ["python3", "node", "npm", "npx", "uv", "uvx"]:
    location = shutil.which(executable)
    print(f"{executable}: {location or 'Not found'}")

# 4. Check Python environment
print("\n[4] Python environment")

print("Python:", os.sys.version.split()[0])
print("Executable:", os.sys.executable)

# 5. Final interpretation
print("\n[5] Result")

if colab_found:
    print("A Colab-related configuration entry was found.")
    print("This does NOT prove the MCP server is connected.")
    print("Next: ask Antigravity to call the Colab tools.")
else:
    print("No Colab entry was found in the inspected locations.")
    print("The configuration may be stored elsewhere.")

print("\nDiagnostic complete.")
