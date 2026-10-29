#!/usr/bin/env bash
set -euo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install_root="${METASKILL_INSTALL_ROOT:-$HOME}"

reject_linked_path() {
    if [ -L "$1" ]; then
        printf 'Unsafe linked install path: %s\n' "$1" >&2
        exit 1
    fi
}

for agent in .qwen .claude; do
    target="$install_root/$agent/skills/metaskill"
    reject_linked_path "$install_root"
    reject_linked_path "$install_root/$agent"
    reject_linked_path "$install_root/$agent/skills"
    if [ -e "$target" ] || [ -L "$target" ]; then
        printf 'Already installed: %s\n' "$target" >&2
        exit 1
    fi
done

for agent in .qwen .claude; do
    target="$install_root/$agent/skills/metaskill"
    reject_linked_path "$install_root"
    reject_linked_path "$install_root/$agent"
    reject_linked_path "$install_root/$agent/skills"
    mkdir -p "$(dirname "$target")"
    reject_linked_path "$(dirname "$target")"
    mkdir "$target"
    cp "$source_dir/SKILL.md" "$source_dir/index.json" "$target/"
    printf 'Installed MetaSkill: %s\n' "$target"
done
