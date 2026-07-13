#!/usr/bin/env python3
"""
NVRAM WIFI bin patcher — enables persistent test mode on MT6639 (connac2).

Sets byte 0x02e0 to 0x01 and recalculates the checksum at offset 0x04.
See findings/01_nvram_patch.md for context, on-device backup steps, and
the rollback procedure.

This script only touches the two local files you give it (input/output).
It does NOT copy anything onto the device — that stays a manual, explicit
`su -c cp ...` step so you always know exactly what got written where.

Usage:
    python3 nvram_patch.py patch  <input_bin> <output_bin>
    python3 nvram_patch.py verify <patched_bin>
    python3 nvram_patch.py revert <backup_bin> <output_bin>

Example (full flow):
    # 1. Pull the LIVE file off the device first — this is your real backup,
    #    not whatever you happen to have lying around on /sdcard.
    su -c "cp /mnt/vendor/nvdata/APCFG/APRDEB/WIFI /sdcard/WIFI_backup.bin"

    # 2. Patch a copy of that backup, never the backup itself.
    python3 nvram_patch.py patch /sdcard/WIFI_backup.bin /sdcard/WIFI_patched.bin

    # 3. Sanity-check the patched file's checksum BEFORE it goes on-device.
    python3 nvram_patch.py verify /sdcard/WIFI_patched.bin

    # 4. Only now copy it onto the device (see findings/01_nvram_patch.md
    #    for the full su/chmod sequence and how to confirm it booted clean).

    # If anything looks wrong after reboot (no WiFi, boot loop, etc.), revert:
    python3 nvram_patch.py revert /sdcard/WIFI_backup.bin /sdcard/WIFI_restore.bin
    su -c "cp /sdcard/WIFI_restore.bin /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
"""

import struct
import sys

PATCH_OFFSET = 0x02e0
PATCH_VALUE = 0x01
CHECKSUM_OFFSET = 0x04


def compute_checksum(data: bytearray) -> int:
    return sum(data[8:]) & 0xFFFFFFFF


def read_checksum(data: bytearray) -> int:
    return struct.unpack_from("<I", data, CHECKSUM_OFFSET)[0]


def load(path: str) -> bytearray:
    with open(path, "rb") as f:
        data = bytearray(f.read())
    if len(data) <= PATCH_OFFSET:
        raise ValueError(
            f"'{path}' is {len(data)} bytes — too small to contain offset {hex(PATCH_OFFSET)}. "
            "This is probably not the right file — did the on-device backup step actually run?"
        )
    return data


def patch(input_path: str, output_path: str) -> None:
    data = load(input_path)

    original_byte = data[PATCH_OFFSET]
    if original_byte == PATCH_VALUE:
        print(f"Note: byte at {hex(PATCH_OFFSET)} is already {hex(PATCH_VALUE)} in the input file.")

    data[PATCH_OFFSET] = PATCH_VALUE
    checksum = compute_checksum(data)
    struct.pack_into("<I", data, CHECKSUM_OFFSET, checksum)

    with open(output_path, "wb") as f:
        f.write(data)

    # Immediately re-read what we just wrote, rather than trusting the in-memory
    # bytearray, so a partial/failed write can't silently pass as "done."
    verify(output_path, expected_patch_value=PATCH_VALUE)

    print(f"\nInput:      {input_path}")
    print(f"Output:     {output_path}")
    print(f"Offset:     {hex(PATCH_OFFSET)}  {hex(original_byte)} -> {hex(PATCH_VALUE)}")
    print(f"Checksum:   {hex(checksum)} (written at {hex(CHECKSUM_OFFSET)})")
    print(
        "\nThis file is NOT yet on the device. Copy it manually with `su -c cp ...`\n"
        "only after you've confirmed you have a separate, untouched backup of the\n"
        "original live file saved somewhere (see the module docstring)."
    )


def verify(path: str, expected_patch_value: int = None) -> None:
    """Re-read a bin file from disk and confirm its stored checksum matches
    what we'd compute fresh, and (optionally) that the patch byte is set."""
    data = load(path)
    stored = read_checksum(data)
    computed = compute_checksum(data)

    ok = stored == computed
    print(f"File:              {path}")
    print(f"Byte at {hex(PATCH_OFFSET)}:      {hex(data[PATCH_OFFSET])}")
    print(f"Stored checksum:   {hex(stored)}")
    print(f"Computed checksum: {hex(computed)}")
    print(f"Checksum match:    {'OK' if ok else 'MISMATCH — do not push this file to the device'}")

    if not ok:
        raise ValueError(
            f"Checksum mismatch in '{path}'. Do not copy this file onto the device — "
            "recheck the patch step or re-derive it from a known-good backup."
        )

    if expected_patch_value is not None and data[PATCH_OFFSET] != expected_patch_value:
        raise ValueError(
            f"Expected byte {hex(PATCH_OFFSET)} to be {hex(expected_patch_value)}, "
            f"found {hex(data[PATCH_OFFSET])}."
        )


def revert(backup_path: str, output_path: str) -> None:
    """Prepare a known-good backup for restoration. This just copies the
    backup through unmodified (after validating it's a plausible bin file)
    so the on-device restore command in the docstring always points at a
    freshly-verified file rather than whatever's sitting on /sdcard."""
    data = load(backup_path)
    stored = read_checksum(data)
    computed = compute_checksum(data)

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"Backup:            {backup_path}")
    print(f"Restore file:      {output_path}")
    print(f"Byte at {hex(PATCH_OFFSET)}:      {hex(data[PATCH_OFFSET])}")
    print(f"Stored checksum:   {hex(stored)}")
    print(f"Computed checksum: {hex(computed)}")
    if stored != computed:
        print(
            "WARNING: this backup's own checksum doesn't validate. It may not be "
            "a clean pre-patch file. Restoring it may not fix a bad boot state."
        )
    print(
        f"\nTo restore on-device:\n"
        f'    su -c "cp {output_path} /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"\n'
        f'    su -c "cp {output_path} /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"\n'
        f'    su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"\n'
        f'    su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"\n'
        f"Then reboot and confirm normal WiFi behavior returns."
    )


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] not in ("patch", "verify", "revert"):
        print(__doc__)
        sys.exit(1)

    cmd = args[0]
    try:
        if cmd == "patch" and len(args) == 3:
            patch(args[1], args[2])
        elif cmd == "verify" and len(args) == 2:
            verify(args[1])
        elif cmd == "revert" and len(args) == 3:
            revert(args[1], args[2])
        else:
            print(__doc__)
            sys.exit(1)
    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
