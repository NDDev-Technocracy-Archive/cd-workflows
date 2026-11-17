from pathlib import Path
import re

for path in Path(".").rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    content = path.read_bytes()
    if b"-----BEGIN " + b"PRIVATE KEY-----" in content:
        raise SystemExit(f"raw private key marker in {path}")
    if re.search(b"gh" + b"[pousr]_[A-Za-z0-9]{30,}", content):
        raise SystemExit(f"raw GitHub token marker in {path}")
