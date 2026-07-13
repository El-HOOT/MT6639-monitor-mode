# Finding 1 — Boot-Persistent Test Mode (NVRAM Patch)

**Status:** CONFIRMED  
**Persistence:** Survives reboot  
**Target:** `/mnt/vendor/nvdata/APCFG/APRDEB/WIFI`

---

Setting byte `0x02e0` from `0x00` to `0x01` enables persistent test mode. The checksum at offset `0x04` must be recalculated or firmware validation rejects the file.

```python
data = bytearray(open('/sdcard/WIFI_original.bin','rb').read())
data[0x02e0] = 0x01
import struct
checksum = sum(data[8:]) & 0xFFFFFFFF
struct.pack_into('<I', data, 4, checksum)
open('/sdcard/WIFI_patched.bin','wb').write(data)
print('Patched:', hex(data[0x2e0]), 'Checksum:', hex(checksum))
```

```bash
su -c "cp /sdcard/WIFI_patched.bin /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
su -c "cp /sdcard/WIFI_patched.bin /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"
su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"
```

Verify:

```bash
su -c "xxd /mnt/vendor/nvdata/APCFG/APRDEB/WIFI | grep '02e0'"
# Expected: 0100 0000...
```

After reboot, `wifitest -O` reports `Already in test mode` — no manual intervention needed.

See [`scripts/nvram_patch.py`](../scripts/nvram_patch.py) for the standalone script.
