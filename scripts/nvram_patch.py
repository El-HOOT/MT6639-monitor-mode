#!/usr/bin/env python3
"""
NVRAM WIFI bin patcher — enables persistent test mode on MT6639 (connac2).

Sets byte 0x02e0 to 0x01 and recalculates the checksum at offset 0x04.
See findings/01_nvram_patch.md for context and manual steps.

Usage:
    python3 nvram_patch.py <input_bin> <output_bin>

Example:
    python3 nvram_patch.py /sdcard/WIFI_original.bin /sdcard/WIFI_patched.bin

After running, push the patched file to the device and set it read-only:
    su -c "cp <output_bin> /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
    su -c "cp <output_bin> /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"
    su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
    su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"
"""

import struct
import sys

PATCH_OFFSET = 0x02e0
PATCH_VALUE = 0x01
CHECKSUM_OFFSET = 0x04


def patch(input_path: str, output_path: str) -> None:
    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    if len(data) <= PATCH_OFFSET:
        raise ValueError(
            f"Input file is {len(data)} bytes — too small to contain offset {hex(PATCH_OFFSET)}"
        )

    original_byte = data[PATCH_OFFSET]
    data[PATCH_OFFSET] = PATCH_VALUE

    checksum = sum(data[8:]) & 0xFFFFFFFF
    struct.pack_into("<I", data, CHECKSUM_OFFSET, checksum)

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"Input:      {input_path}")
    print(f"Output:     {output_path}")
    print(f"Offset:     {hex(PATCH_OFFSET)}  {hex(original_byte)} -> {hex(PATCH_VALUE)}")
    print(f"Checksum:   {hex(checksum)} (written at {hex(CHECKSUM_OFFSET)})")


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    patch(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
