#!/usr/bin/env bash
set -euo pipefail

# Only edit these 2 lines
PI_IP="10.12.194.1"
SSH_PRIVATE_KEY="$HOME/.ssh/pqc_rescue_pi_ssh"

PI_HOST="pqcadmin@$PI_IP"
REMOTE_DIR="/var/lib/pqc-rescue/incoming"

if [[ ! -f "$SSH_PRIVATE_KEY" ]]; then
    echo "SSH private key not found at: $SSH_PRIVATE_KEY" >&2
    exit 1
fi

PACKAGE="${1:?Usage: $0 path/to/update.tar.gz}"
PACKAGE="$(realpath -- "$PACKAGE")"

if [[ ! -f "$PACKAGE" ]]; then
    echo "Package not found at: $PACKAGE" >&2
    exit 1
fi

PACKAGE_NAME="$(basename -- "$PACKAGE")"
REMOTE_PART="$REMOTE_DIR/$PACKAGE_NAME.part"
REMOTE_FINAL="$REMOTE_DIR/$PACKAGE_NAME"

echo "Uploading $PACKAGE_NAME..."

sftp \
    -i "$SSH_PRIVATE_KEY" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -b - \
    "$PI_HOST" <<EOF
put "$PACKAGE" "$REMOTE_PART"
rename "$REMOTE_PART" "$REMOTE_FINAL"
EOF

echo "Update uploaded successfully:"
echo "$REMOTE_FINAL"
