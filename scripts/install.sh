#!/usr/bin/env bash
set -euo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install_root="${METASKILL_INSTALL_ROOT:-$HOME}"

for agent in .qwen .claude; do
    target="$install_root/$agent/skills/metaskill"
    if [ -e "$target" ] || [ -L "$target" ]; then
        printf 'Already installed: %s\n' "$target" >&2
        exit 1
    fi
done

for agent in .qwen .claude; do
    target="$install_root/$agent/skills/metaskill"
    mkdir -p "$(dirname "$target")"
    mkdir "$target"
    cp "$source_dir/SKILL.md" "$source_dir/index.json" "$target/"
    printf 'Installed MetaSkill: %s\n' "$target"
done
