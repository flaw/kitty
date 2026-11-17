#!/usr/bin/env bash
# Build/sign inside Nix, then cleanly replace a local macOS app installation.
set -euo pipefail

usage() {
    printf '%s\n' \
        'Usage: ./local-install.sh [DESTINATION.app]' \
        'Default: /Applications/Kitty-Custom.app (or KITTY_INSTALL_DEST)' \
        'Builds using shell.nix, signs with SIGN_IDENTITY, and keeps the previous app as a backup.' \
        'Quit the destination app first; this script never quits it for you.'
}
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
    usage
    exit 0
fi
if [[ $# -gt 1 || "$(uname -s)" != Darwin ]]; then
    usage >&2
    exit 1
fi

REPO="$(cd -- "$(dirname -- "$0")" && pwd -P)"
DEST="${1:-${KITTY_INSTALL_DEST:-/Applications/Kitty-Custom.app}}"
IDENTITY="${SIGN_IDENTITY-Kitty Local Development}"
if [[ "$DEST" != /* || "$DEST" != *.app || -L "$DEST" ]]; then
    printf 'Destination must be an absolute, non-symlink .app path: %s\n' "$DEST" >&2
    exit 1
fi
if [[ "$DEST" == "$REPO/kitty.app" || "$DEST" == "$REPO/kitty/launcher/kitty.app" ]]; then
    printf 'Destination must not be a build output.\n' >&2
    exit 1
fi
if [[ -e "$DEST" && ! -f "$DEST/Contents/Info.plist" ]]; then
    printf 'Refusing to replace a destination that is not an app bundle: %s\n' "$DEST" >&2
    exit 1
fi
check_not_running() {
    local process
    while IFS= read -r process; do
        case "$process" in
            "$DEST/Contents/"*)
                printf 'Quit %s before installing (including its helper panels). Run this from Terminal.app if needed.\n' "$DEST" >&2
                return 1
                ;;
        esac
    done < <(/bin/ps -ax -o comm=)
}
check_not_running

NIX_SHELL="${NIX_SHELL:-nix-shell}"
cd "$REPO"
SIGN_IDENTITY="$IDENTITY" "$NIX_SHELL" "$REPO/shell.nix" --run 'make app'
check_not_running

PARENT="$(dirname -- "$DEST")"
mkdir -p -- "$PARENT"
STAGING="$(mktemp -d "$PARENT/.kitty-local-install.XXXXXX")"
BACKUP=
cleanup() {
    local status=$?
    if [[ $status -ne 0 && -n "$BACKUP" && ! -e "$DEST" && -e "$BACKUP" ]]; then
        mv -- "$BACKUP" "$DEST" || printf 'Rollback failed; previous app is at %s\n' "$BACKUP" >&2
    fi
    rm -rf -- "$STAGING"
    exit "$status"
}
trap cleanup EXIT

# Copy into an empty location, not over the old bundle: ditto merges existing trees.
STAGED="$STAGING/$(basename -- "$DEST")"
/usr/bin/ditto "$REPO/kitty.app" "$STAGED"
if [[ -n "$IDENTITY" ]]; then
    /usr/bin/codesign --verify --deep --strict --verbose=2 "$STAGED"
fi
check_not_running
if [[ -e "$DEST" ]]; then
    BACKUP="${DEST%.app}.backup-$(date +%Y%m%d-%H%M%S)-$$.app"
    mv -- "$DEST" "$BACKUP"
fi
mv -- "$STAGED" "$DEST"
printf 'Installed: %s\n' "$DEST"
if [[ -n "$BACKUP" ]]; then
    printf 'Previous app: %s\n' "$BACKUP"
fi
printf 'Open with: open %q\n' "$DEST"
