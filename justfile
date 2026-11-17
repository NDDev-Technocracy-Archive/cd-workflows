set shell := ["bash", "-euo", "pipefail", "-c"]

# Lists the commands.
default:
    @just --list

# Checks schemas, trust/catalog/source contracts and workflows without builds or network.
check:
    just --fmt --check
    python3 scripts/cd_contract.py validate-schema
    python3 scripts/check_structure.py
    python3 scripts/check_action_catalog.py
    python3 scripts/check_public_source.py
    bash -n scripts/validate_module.sh
    actionlint .github/workflows/ci.yml .github/workflows/release.yml .github/workflows/security.yml
    zizmor --offline --no-progress .github/workflows/ci.yml .github/workflows/release.yml .github/workflows/security.yml
    gitleaks git --no-banner --redact --log-opts=--all .
    git diff --check

# Formats the command file.
fix:
    just --fmt

# Runs every original unit/provenance case and Python bytecode qualification.
test:
    python3 -m unittest discover -s tests -v
    python3 -m py_compile scripts/cd_contract.py tests/test_cd_contract.py tests/test_contract_sha_provenance.py

# Runs every source and native contract check without a delivery operation.
verify: check test
