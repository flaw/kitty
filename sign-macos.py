#!/usr/bin/env python3
# License: GPLv3 Copyright: 2026, Kovid Goyal <kovid at kovidgoyal.net>
"""Sign a local macOS build without changing external dependencies or keychains."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

MACH_O_MAGIC = frozenset(
    (
        b'\xfe\xed\xfa\xce',
        b'\xce\xfa\xed\xfe',
        b'\xfe\xed\xfa\xcf',
        b'\xcf\xfa\xed\xfe',
        b'\xca\xfe\xba\xbe',
        b'\xbe\xba\xfe\xca',
        b'\xca\xfe\xba\xbf',
        b'\xbf\xba\xfe\xca',
    )
)


def signing_targets(app: Path) -> list[Path]:
    """Return real Mach-O files, then nested bundles, then the app itself."""
    binaries: list[Path] = []
    bundles: list[Path] = []
    for directory, dirs, files in os.walk(app, followlinks=False):
        root = Path(directory)
        # Never follow symlinks into the checkout, Nix store, or framework aliases.
        dirs[:] = sorted(d for d in dirs if not (root / d).is_symlink())
        if root != app and root.suffix in ('.app', '.framework', '.xpc', '.appex', '.bundle'):
            bundles.append(root)
        for name in sorted(files):
            path = root / name
            if path.is_symlink() or not path.is_file():
                continue
            with path.open('rb') as stream:
                if stream.read(4) in MACH_O_MAGIC:
                    binaries.append(path)
    bundles.sort(key=lambda path: (-len(path.parts), str(path)))
    return binaries + bundles + [app]


def sign_app(app: Path, identity: str) -> None:
    if not identity.strip():
        raise ValueError('Specify a signing identity, or - for ad-hoc signing')
    if app.is_symlink() or not (app / 'Contents' / 'Info.plist').is_file():
        raise ValueError(f'Not a regular macOS app bundle: {app}')
    app = app.absolute()
    for target in signing_targets(app):
        print(f'Signing {target}', flush=True)
        subprocess.run(['/usr/bin/codesign', '--force', '--timestamp=none', '--sign', identity, str(target)], check=True)
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(app)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity', required=True, help='Keychain identity name/hash, or - for ad-hoc signing')
    parser.add_argument('app', type=Path, nargs='?', default=Path('kitty.app'))
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('Code signing is only supported on macOS')
    try:
        sign_app(args.app, args.identity)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Signing failed: {error}\n')


if __name__ == '__main__':
    main()
