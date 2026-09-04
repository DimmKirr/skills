#!/usr/bin/env bash
# Remove every graphics placement from the user's terminal.
# a=d,d=A deletes all placements and frees the stored image data. Needed for
# strays transmitted without an id, which cannot be targeted individually.
set -uo pipefail
dev=${TTY_IMAGE_DEV:-/dev/pts/0}
tmpf=$(mktemp /tmp/ttyclear.XXXXXX)
trap 'rm -f "$tmpf"' EXIT
printf '\033Ptmux;\033\033_Ga=d,d=A;\033\033\\\033\\' > "$tmpf"
sudo sh -c "cat '$tmpf' > '$dev'"
echo "cleared all images on $dev"
