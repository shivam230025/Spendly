import json
import re
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

# Matches a .db path anywhere in the command (bash, python, powershell all
# reference the filename as a plain token, quoted or not).
DB_REF = r"[\w./\\-]*\.db\b"

# Dangerous regardless of whether a literal .db filename shows up in the
# same command (e.g. SQL against an already-open connection or a $DB_FILE
# env var).
SQL_DANGEROUS_PATTERNS = [
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+DATABASE\b",
    r"\bDELETE\s+FROM\s+\S+(?!.*\bWHERE\b)",  # DELETE with no WHERE clause
]

# Verbs/APIs across bash, python, and powershell that can delete, truncate,
# or relocate a file. These only count as dangerous when paired with a .db
# reference in the same command -- otherwise "rm" alone would block
# everything.
FILE_DANGEROUS_PATTERNS = [
    r"\brm\b",
    r"\bdel\b",
    r"\berase\b",
    r"\bunlink\b",
    r"\bmv\b",
    r"\bremove-item\b",
    r"\bmove-item\b",
    r"\bclear-content\b",
    r"\bset-content\b",
    r"\bout-file\b",
    r"os\.(remove|unlink)\s*\(",
    r"shutil\.rmtree\s*\(",
    r"\.unlink\s*\(",
    r">\s*\S*\.db\b",  # shell truncation/overwrite redirect
]


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }))
    sys.exit(0)


for pattern in SQL_DANGEROUS_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        deny(f"Blocked: command matches dangerous database pattern ({pattern})")

if re.search(DB_REF, command, re.IGNORECASE):
    for pattern in FILE_DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            deny(f"Blocked: command references a .db file alongside a destructive operation ({pattern})")

# Allow everything else
sys.exit(0)
