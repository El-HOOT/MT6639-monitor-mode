#!/data/data/com.termux/files/usr/bin/bash
#
# Sets up the Termux environment for MT6639 monitor mode research.
# Installs required packages and stages root-accessible copies of
# binaries needed by findings/02 through 07.
#
# Usage: bash setup_termux.sh

set -e

echo "[*] Installing packages..."
pkg install tcpdump xxd iw wireless-tools strace python3 -y

echo "[*] Staging binaries to /data/local/tmp..."
BIN_DIR="/data/data/com.termux/files/usr/bin"
DEST="/data/local/tmp"

for bin in iwpriv iw strace python3; do
    if [ -f "$BIN_DIR/$bin" ]; then
        su -c "cp $BIN_DIR/$bin $DEST/$bin"
        su -c "chmod 755 $DEST/$bin"
        echo "    staged: $bin"
    else
        echo "    WARNING: $bin not found in $BIN_DIR — skipping"
    fi
done

echo "[*] Verifying vendor test tool exists..."
if su -c "test -f /vendor/bin/wifitest"; then
    echo "    /vendor/bin/wifitest found"
else
    echo "    WARNING: /vendor/bin/wifitest not found — this chip/ROM may not expose it"
fi

echo "[*] Setup complete. See findings/ for next steps."
