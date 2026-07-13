# MT6639 (connac2) — WiFi Monitor Mode & Frame Injection Research

Hardware-level WiFi capability research on a **MediaTek Dimensity 7300 (MT6878)** device with **MT6639 connac2** WiFi/BT combo chip.

The standard `cfg80211` interface does not advertise monitor mode for this chip. This research documents that monitor-equivalent capture, hardware RF monitoring, and frame injection are nonetheless reachable via vendor factory tooling and proprietary driver ioctls present in the **production firmware**.

> **Status:** Personal research archive. Not a disclosure document, not a how-to guide.  
> **Root method:** KernelSU  
> **Date:** July 2026

---

## Capability Summary

| Capability | Status | Method |
|---|---|---|
| Promiscuous Mode | `set_sw_ctrl` + tcpdump |
| Hardware RF Monitor | `wifitest -r` (frame counts + RSSI) |
| Hardware TX Injection | `wifitest -t` (100% success rate) |
| Firmware Log Access | `/dev/fw_log_wifi` |
| Kernel Packet Trace | `connsys_trace_event` (1913 entries) |
| Boot-Persistent Config | NVRAM patch at `0x02e0` + test mode |
| Raw 802.11 Frame Dump | ⚠️ PARTIAL | BB1 buffer hardcoded at `0x7E4` — too small |
| EAPOL Frame Visibility | Via promiscuous capture — see disclaimer |

---

## Device

| Component | Detail |
|---|---|
| SoC | MediaTek Dimensity 7300 (MT6878) |
| WiFi/BT Chip | MediaTek MT6639 (connac2) |
| WiFi Driver | wlan_drv_gen4m_6878 (4th gen proprietary) |
| Kernel Stack | conninfra → wmt_chrdev_wifi_connac2 → wlan_drv_gen4m_6878 → cfg80211 |
| Firmware | soc7_0_ram_mcu (build: 2021-12-06, ALPS) |
| WiFi Standard | WiFi 6 (802.11ax), 2x2 MIMO, 2.4GHz + 5GHz |
| Declared Modes | managed, AP, P2P-client, P2P-GO — **monitor NOT listed** |

---

## Reproducing This Research

### Requirements

- Android device with MT6639 / connac2 chip
- Root access (KernelSU or Magisk)
- Termux

### 1. Install dependencies

```bash
pkg install tcpdump xxd iw wireless-tools strace python3 -y
```

### 2. Stage binaries

```bash
su -c "cp /data/data/com.termux/files/usr/bin/iwpriv /data/local/tmp/iwpriv"
su -c "cp /data/data/com.termux/files/usr/bin/iw /data/local/tmp/iw"
su -c "cp /data/data/com.termux/files/usr/bin/strace /data/local/tmp/strace"
su -c "chmod 755 /data/local/tmp/iwpriv /data/local/tmp/iw /data/local/tmp/strace"
```

Or run [`scripts/setup_termux.sh`](scripts/setup_termux.sh) directly.

### 3. Follow findings in order

Each finding is self-contained in [`findings/`](findings/). Start with the NVRAM patch if you want persistent test mode, or jump to a specific capability.

---

## Repository Structure

```
MT6639-monitor-mode/
├── README.md
├── DISCLAIMER.md
│
├── findings/
│   ├── 01_nvram_patch.md       # Persistent test mode via WIFI bin patch
│   ├── 02_promiscuous.md       # set_sw_ctrl — accidental promiscuous capture
│   ├── 03_rf_monitor.md        # wifitest -r — hardware RF monitor
│   ├── 04_tx_injection.md      # wifitest -t — frame injection
│   ├── 05_fw_log.md            # /dev/fw_log_wifi — firmware log stream
│   ├── 06_kernel_trace.md      # connsys_trace_event — kernel packet trace
│   └── 07_ioctl_reference.md   # Full iwpriv table + strace ioctl map
│
├── scripts/
│   ├── nvram_patch.py          # WIFI bin patcher (offset 0x02e0 + checksum)
│   └── setup_termux.sh         # Dependency install + binary staging
│
└── reference/
    ├── vendor_tools.md         # wifitest, wlan_assistant, wifi_dump, wmt_*
    └── key_files.md            # /dev paths, /sys paths, firmware locations
```

---

## Key Technical Points

- **`cfg80211` lies.** Monitor mode is not in the declared interface list, but the firmware contains `IDLM monitor` strings and a `Monitor Duration` timer — the code path exists, it just isn't surfaced through the standard stack.
- **`set_sw_ctrl` is undocumented.** No public source describes what ioctl `0x0014` does. Running it produced promiscuous-mode Ethernet-layer capture — an outcome I did not anticipate.
- **`set_oid` will kernel panic.** Issuing ioctl `0x8BEF` with an unknown OID caused a full crash. Don't touch it without exact register knowledge.
- **Vendor tooling bypasses nl80211 entirely.** `wifitest`, `wlan_assistant`, and `wifi_dump` have direct hardware register access. For this chip family, they are the real research surface.
- **The NVRAM patch survives reboot.** Setting byte `0x02e0 = 0x01` in `/mnt/vendor/nvdata/APCFG/APRDEB/WIFI` (with checksum recalculated) causes the chip to boot directly into test mode on every subsequent boot.

---

## Disclaimer

The promiscuous-mode finding was accidental. Running `set_sw_ctrl` to test an undocumented ioctl resulted in third-party traffic becoming visible — including EAPOL handshake frames from other clients on the network. This was not the goal of the test. No third-party traffic was retained, analyzed, or acted on beyond confirming the finding exists.

See [`DISCLAIMER.md`](DISCLAIMER.md) for the full scope and ethics statement.

---

## References

- MediaTek connac2 driver: `wlan_drv_gen4m_6878` (in-kernel, proprietary)
- [`/proc/net/dev`](reference/key_files.md) — interface enumeration
- [iwpriv private ioctl table](findings/07_ioctl_reference.md)
- [Vendor tool inventory](reference/vendor_tools.md)

---

## License

Research and documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
Scripts: MIT
