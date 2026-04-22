#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "GitHub Secrets Exporter"
echo "=========================================="
echo ""

for cmd in age age-keygen gh git mktemp; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: '$cmd' is not installed."
        exit 1
    fi
done

ORIGINAL_DIR="$(pwd)"
ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

WORKFLOW_FILE=".github/workflows/export-secrets.yml"
BRANCH_NAME="export-secrets-$(date +%s)"
RANDOM_HEX="$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')"
OUTPUT_ENV="$ORIGINAL_DIR/.env.export.$RANDOM_HEX"


TEMP_DIR="$(mktemp -d)"
PRIVATE_KEY="$TEMP_DIR/private.key"
RUN_ID=""
PR_URL=""
WORKFLOW_EXISTED_BEFORE="false"
REMOTE_BRANCH_DELETED="false"

if [ -f "$WORKFLOW_FILE" ]; then
    WORKFLOW_EXISTED_BEFORE="true"
fi

cleanup() {
    set +e

    cd "$ORIGINAL_DIR" >/dev/null 2>&1 || true

    echo ""
    echo "Cleanup..."
    echo ""

    if [ -n "${PR_URL:-}" ]; then
        gh pr close "$PR_URL" --repo "$REPO" >/dev/null 2>&1 || true
    fi

    if [ -n "${RUN_ID:-}" ] && [ "$RUN_ID" != "null" ]; then
        gh run delete "$RUN_ID" --repo "$REPO" >/dev/null 2>&1 || true
    fi

    git checkout "$ORIGINAL_BRANCH" >/dev/null 2>&1 || true
    git branch -D "$BRANCH_NAME" >/dev/null 2>&1 || true

    if [ "$REMOTE_BRANCH_DELETED" != "true" ]; then
        git push origin --delete "$BRANCH_NAME" >/dev/null 2>&1 || true
    fi

    if [ "$WORKFLOW_EXISTED_BEFORE" = "false" ]; then
        rm -f "$WORKFLOW_FILE"
        rmdir --ignore-fail-on-non-empty .github/workflows >/dev/null 2>&1 || true
        rmdir --ignore-fail-on-non-empty .github >/dev/null 2>&1 || true
    fi

    rm -rf "$TEMP_DIR"

    echo "✓ Temporary files removed"
}
trap cleanup EXIT INT TERM

echo "Step 1: Generate encryption key"
echo "================================"
echo ""

age-keygen -o "$PRIVATE_KEY" >/dev/null
chmod 600 "$PRIVATE_KEY"

PUBLIC_KEY="$(grep '^# public key:' "$PRIVATE_KEY" | awk '{print $4}')"

if [ -z "${PUBLIC_KEY:-}" ]; then
    echo "Error: Could not extract public key"
    exit 1
fi

echo "✓ Public key: $PUBLIC_KEY"
echo ""

echo "Step 2: Create workflow file"
echo "============================="
echo ""

if [ -f "$WORKFLOW_FILE" ]; then
    echo "Warning: $WORKFLOW_FILE already exists!"
    read -r -p "Do you want to overwrite it? (y/N) " REPLY
    if [[ ! "${REPLY:-}" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

mkdir -p .github/workflows

cat > "$WORKFLOW_FILE" <<EOF
name: Export Secrets
on: pull_request

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: gerrywastaken/github-secrets-exporter@v1.1
        with:
          secrets_json: \${{ toJSON(secrets) }}
          public_encryption_key: '$PUBLIC_KEY'
EOF

echo "✓ Created $WORKFLOW_FILE"
echo ""

echo "Step 3: Create PR and trigger workflow"
echo "======================================="
echo ""

git checkout -b "$BRANCH_NAME"
git add "$WORKFLOW_FILE"
git commit -m "DO NOT MERGE: Export secrets"
git push -u origin "$BRANCH_NAME"

echo ""
echo "Creating pull request..."

PR_URL="$(gh pr create \
  --repo "$REPO" \
  --title "DO NOT MERGE: Export secrets" \
  --body "Temporary PR to trigger export-secrets workflow" \
  --base "$ORIGINAL_BRANCH" \
  --head "$BRANCH_NAME")"

echo "✓ PR created: $PR_URL"
echo ""

echo "Step 4: Watch workflow and download artifact"
echo "============================================="
echo ""

MAX_RETRIES=20
RETRY_DELAY=3

for i in $(seq 1 "$MAX_RETRIES"); do
    RUN_ID="$(gh run list \
      --repo "$REPO" \
      --branch "$BRANCH_NAME" \
      --workflow=export-secrets.yml \
      --limit 1 \
      --json databaseId \
      --jq '.[0].databaseId' 2>/dev/null || true)"

    if [ -n "${RUN_ID:-}" ] && [ "$RUN_ID" != "null" ]; then
        echo "✓ Workflow run detected (ID: $RUN_ID)"
        break
    fi

    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "Error: Workflow run not found"
        exit 1
    fi

    echo "Waiting for workflow to appear... ($i/$MAX_RETRIES)"
    sleep "$RETRY_DELAY"
done

echo ""

if ! gh run watch "$RUN_ID" --repo "$REPO"; then
    echo "Note: run watch returned non-zero. Trying download anyway..."
fi

echo ""
echo "Downloading encrypted secrets..."

gh run download "$RUN_ID" --repo "$REPO" --name encrypted-secrets -D "$TEMP_DIR"

if [ ! -f "$TEMP_DIR/encrypted-secrets.age" ]; then
    echo "Error: encrypted-secrets.age was not downloaded"
    exit 1
fi

echo "✓ Encrypted artifact downloaded"
echo ""

echo "Step 5: Convert decrypted secrets to .env file"
echo "==============================================="
echo ""

DECRYPTED_JSON="$TEMP_DIR/secrets.json"

age --decrypt --identity "$PRIVATE_KEY" < "$TEMP_DIR/encrypted-secrets.age" > "$DECRYPTED_JSON"

python3 - "$DECRYPTED_JSON" "$OUTPUT_ENV" <<'PY'
import json
import re
import sys

input_path = sys.argv[1]
output_path = sys.argv[2]

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def normalize_key(key: str) -> str:
    key = re.sub(r'[^A-Za-z0-9_]', '_', key)
    if not re.match(r'^[A-Za-z_]', key):
        key = "_" + key
    return key

def encode_value(value) -> str:
    if value is None:
        return "''"
    s = str(value)
    s = s.replace("\\", "\\\\")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace('"', '\\"')
    return f"\"{s}\""

with open(output_path, "w", encoding="utf-8") as out:
    for k, v in data.items():
        out.write(f"{normalize_key(k)}={encode_value(v)}\n")
PY

chmod 600 "$OUTPUT_ENV"

echo "✓ Secrets saved to: $OUTPUT_ENV"
echo ""
echo "Add this pattern to .gitignore if needed:"
echo "  .env.export.*"
echo ""
read -r -p "Press Enter to finish cleanup..."

echo ""
echo "Done."