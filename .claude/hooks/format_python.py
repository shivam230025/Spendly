import sys
import json
import subprocess

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")

if file_path.endswith(".py"):
    subprocess.run(["python", "-m", "black", "--quiet", file_path])