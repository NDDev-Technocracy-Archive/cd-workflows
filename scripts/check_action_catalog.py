# Every pinned action must match catalog/actions.yml exactly: the SHA and the
# release its comment names. A comment nobody compares is a comment that
# drifts, and this one did -- fifteen checkout pins said v5.0.0 while the SHA
# was v7.0.1, two majors apart, on the module that deploys the fleet.
from pathlib import Path
import re

# Read strictly, by column. The first version of this stripped every line and
# looked for `- name:` anywhere, which ignores indentation entirely -- so a
# catalog that no YAML parser will load still "read fine" and the whole check
# below passed on it. That was found by mis-indenting an entry by two spaces:
# `yaml.safe_load` raised `expected <block end>`, and this script printed OK.
# The module ships no dependencies, so the answer is not PyYAML; it is refusing
# any shape other than the one shape this file is allowed to have.
registry = {}
current = {}
catalog = Path("catalog/actions.yml")
in_actions = False
for number, line in enumerate(catalog.read_text(encoding="utf-8").splitlines(), 1):
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    if not in_actions:
        in_actions = line == "actions:"
        continue
    if line.startswith("  - name: "):
        if current:
            registry[current["name"]] = current
        current = {"name": line[len("  - name: "):].strip().strip('"')}
    elif line.startswith("    sha: ") and current:
        current["sha"] = line[len("    sha: "):].strip().strip('"')
    elif line.startswith("    version: ") and current:
        current["version"] = line[len("    version: "):].strip().strip('"')
    else:
        raise SystemExit(
            f"{catalog}:{number}: catalog entries are exactly "
            f'`  - name: X` / `    sha: \"…\"` / `    version: \"…\"`; got {line!r}'
        )
if current:
    registry[current["name"]] = current
if not registry:
    raise SystemExit(f"{catalog}: declares no actions; refusing to pass a check with nothing to check")
for name, entry in sorted(registry.items()):
    missing = [k for k in ("sha", "version") if k not in entry]
    if missing:
        raise SystemExit(f"{catalog}: {name} is missing {', '.join(missing)}")
    if len(entry["sha"]) != 40:
        raise SystemExit(f"{catalog}: {name} records a {len(entry['sha'])}-character SHA, expected 40")

pattern = re.compile(r"uses:\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)@([0-9a-f]{40})\s*#\s*(\S+)")
seen = set()
for path in sorted(Path(".github").rglob("*.yml")):
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if "uses:" not in line or "@" not in line:
            continue
        if re.search(r"uses:\s+\./", line):
            continue
        match = pattern.search(line)
        if match is None:
            raise SystemExit(f"{path}:{number}: pinned action needs a 40-character SHA and a version comment")
        name, sha, version = match.groups()
        entry = registry.get(name)
        if entry is None:
            raise SystemExit(f"{path}:{number}: {name} is not declared in catalog/actions.yml")
        if sha != entry["sha"]:
            raise SystemExit(f"{path}:{number}: {name} pins {sha[:12]} but the catalog records {entry['sha'][:12]}")
        if version != entry["version"]:
            raise SystemExit(f"{path}:{number}: {name} comment says {version} but the catalog records {entry['version']} for this SHA")
        seen.add(name)

unused = sorted(set(registry) - seen)
if unused:
    raise SystemExit(f"catalog/actions.yml declares actions nothing uses: {unused}")
