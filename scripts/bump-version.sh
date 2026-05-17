#!/usr/bin/env bash
# Atomic version bump across every manifest listed in .version-bump.json.
# Usage: ./scripts/bump-version.sh <new-version>
# Example: ./scripts/bump-version.sh 1.0.1

set -euo pipefail

NEW_VERSION="${1:-}"

if [[ -z "$NEW_VERSION" ]]; then
  echo "Usage: $0 <new-version>" >&2
  echo "Example: $0 1.0.1" >&2
  exit 1
fi

if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
  echo "Error: '$NEW_VERSION' is not a valid semver" >&2
  exit 1
fi

CONFIG="${BUMP_CONFIG:-.version-bump.json}"

if [[ ! -f "$CONFIG" ]]; then
  echo "Error: $CONFIG not found (run from repo root)" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required (https://stedolan.github.io/jq/)" >&2
  exit 1
fi

count=0
jq -c '.files[]' "$CONFIG" | while read -r entry; do
  path=$(echo "$entry" | jq -r '.path')
  field=$(echo "$entry" | jq -r '.field')

  if [[ ! -f "$path" ]]; then
    echo "  skip: $path (file missing)" >&2
    continue
  fi

  # Translate dotted field paths like "plugins.0.version" -> jq's "plugins[0].version"
  jq_path=$(echo "$field" | sed -E 's/\.([0-9]+)/[\1]/g')
  tmp=$(mktemp)
  if jq ".${jq_path} = \"${NEW_VERSION}\"" "$path" >"$tmp"; then
    mv "$tmp" "$path"
    echo "  bump: $path .${jq_path} -> ${NEW_VERSION}"
    count=$((count + 1))
  else
    rm -f "$tmp"
    echo "  fail: $path .${jq_path}" >&2
    exit 1
  fi
done

echo
echo "Version bumped to ${NEW_VERSION} across all manifests."
echo "Review the diff: git diff"
echo "Commit:          git commit -am \"chore: bump to v${NEW_VERSION}\""
echo "Tag:             git tag v${NEW_VERSION} && git push --tags"
