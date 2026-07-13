# MT6639 (connac2) — WiFi Hardware Research

## Monitor Mode & Frame Injection on MediaTek Dimensity 7300 (MT6878 / MT6639 connac2)

**Date:** July 2026
**Platform:** Android / KernelSU / Termux
**Status:** Personal research archive — not a disclosure document, not a how-to guide

---

## Capability Summary

| Capability | Status | Method |
|---|---|---|
| Promiscuous Mode | UNLOCKED | `set_sw_ctrl` + tcpdump |
| Hardware RF Monitor | UNLOCKED | `wifitest -r` (stats + frame counts) |
| Hardware TX Injection | UNLOCKED | `wifitest -t` (100% success rate) |
| Firmware Log Access | UNLOCKED | `/dev/fw_log_wifi` |
| Kernel Packet Trace | UNLOCKED | `connsys_trace_event` (1913 entries) |
| Raw 802.11 Frame Dump | PARTIAL | Firmware BB1 buffer too small (0x7E4) |
| EAPOL Frame Visibility | UNLOCKED (accidental) | Encountered via promiscuous mode capture — see disclosure note |
| Boot-Persistent Config | UNLOCKED | WIFI bin patch at 0x02e0 + test mode |

This document reports hardware-level WiFi capability research on a device with a MediaTek Dimensity 7300 SoC and MT6639 WiFi/BT combo chip (connac2 generation), performed on a device under my control via root access (KernelSU), vendor factory test tooling, and kernel instrumentation.

---

## Scope Note

This is a record of interacting with an undocumented chip interface to determine its behavior, not a polished disclosure.

Running `set_sw_ctrl` was a test of an undocumented private ioctl's function. It was not undertaken with the expectation, or intent, of surfacing third-party traffic. When traffic from other MAC addresses — including other clients' EAPOL handshake frames — became visible on the interface, that outcome was unanticipated. No captured third-party traffic was retained, analyzed, or used beyond confirming which frame types were passing through. Full detail in `DISCLAIMER.md`.

---

## Why This Matters

- **For device owners:** `cfg80211` does not list monitor mode as a supported interface type on this chip, but the underlying firmware and driver expose ioctls that produce monitor-equivalent and injection behavior regardless. This capability is invisible from the standard Android/Linux wireless stack.
- **For security researchers:** vendor factory test tooling (`wifitest`, private ioctls) provides a materially different capability surface than the declared `cfg80211` interface list. `set_sw_ctrl`, `wifitest -r`, and `wifitest -t` are reachable with root on MediaTek connac2-generation chips regardless of what the kernel driver advertises.
- **For MediaTek:** a promiscuous-capture path that can be triggered without full documentation of its side effects, and that captures third-party frames including EAPOL handshakes, is worth internal review — both from a gating perspective and an intended-design perspective. Nothing has been filed with MediaTek at this time.

This is not a specific CVE-level vulnerability claim. It is an assertion that this chip's real capability surface diverges substantially from its declared one, that the divergence was reachable with commodity root tooling, and that this has implications for anyone treating `cfg80211`'s mode list as authoritative.

---

## [1] Device Specifications

| Component | Detail |
|---|---|
| SoC | MediaTek Dimensity 7300 (MT6878) |
| WiFi/BT Chip | MediaTek MT6639 (connac2 generation) |
| WiFi Driver | wlan_drv_gen4m_6878 (4th gen proprietary MediaTek) |
| Kernel Stack | conninfra → wmt_chrdev_wifi_connac2 → wlan_drv_gen4m_6878 → cfg80211 |
| Firmware | soc7_0_ram_mcu (build: 2021-12-06, ALPS platform) |
| WiFi Standard | WiFi 6 (802.11ax), 2x2 MIMO, 2.4GHz + 5GHz |
| Declared Modes | managed, AP, P2P-client, P2P-GO (monitor NOT listed in cfg80211) |
| Firmware Strings | IDLM monitor, Monitor Duration timer, BB1 packet logging |
| Root Method | KernelSU |

The official `cfg80211` interface mode list does not advertise monitor mode. This research demonstrates that monitor-equivalent and injection capabilities are nonetheless reachable via vendor factory test tooling and driver ioctls present in production firmware.

---

## [2] Research Environment

```bash
pkg install tcpdump xxd iw wireless-tools strace python3 -y
```

```bash
su -c "cp /data/data/com.termux/files/usr/bin/iwpriv /data/local/tmp/iwpriv"
su -c "cp /data/data/com.termux/files/usr/bin/iw /data/local/tmp/iw"
su -c "cp /data/data/com.termux/files/usr/bin/strace /data/local/tmp/strace"
su -c "cp /data/data/com.termux/files/usr/bin/python3 /data/local/tmp/python3"
su -c "chmod 755 /data/local/tmp/iwpriv /data/local/tmp/iw /data/local/tmp/strace /data/local/tmp/python3"
```

---

## [3] Finding 1 — WiFi Firmware Config Patch (Persistent Test Mode)

**CONFIRMED** — NVRAM firmware config patched; chip boots into test mode on every subsequent boot.

Target file: `/mnt/vendor/nvdata/APCFG/APRDEB/WIFI`

Byte `0x02e0` set from `0x00` to `0x01` enables persistent test mode. The checksum field at offset `0x04` is a running sum of all bytes from offset 8 onward, masked to 32 bits, and must be recalculated to pass firmware validation.

```python
python3 -c "
data = bytearray(open('/sdcard/WIFI_original.bin','rb').read())
data[0x02e0] = 0x01
import struct
checksum = sum(data[8:]) & 0xFFFFFFFF
struct.pack_into('<I', data, 4, checksum)
open('/sdcard/WIFI_patched.bin','wb').write(data)
print('Patched at 0x2e0:', hex(data[0x2e0]), 'Checksum:', hex(checksum))
"
```

```bash
su -c "cp /sdcard/WIFI_patched.bin /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
su -c "cp /sdcard/WIFI_patched.bin /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"
su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI"
su -c "chmod 444 /mnt/vendor/nvdata/APCFG/APRDEB/WIFI.bak"
```

Verification:

```bash
su -c "xxd /mnt/vendor/nvdata/APCFG/APRDEB/WIFI | grep '02e0'"
# Expected: 0100 0000...
```

**Key result:** After patching, `wifitest -O` reports "Already in test mode" — confirming the patch persists across reboots and that firmware validates and applies the config on boot. The `.bak` copy is written because the NVRAM partition's own consistency checker will restore from backup if the primary file fails validation; keeping both in sync avoids a silent revert.

---

## [4] Finding 2 — Promiscuous Mode (Ethernet-level Capture) — Accidental Discovery

**CONFIRMED** — Promiscuous mode unlocked via `set_sw_ctrl` ioctl. Not the intended outcome of the test.

The driver exposes a private ioctl `set_sw_ctrl` (ioctl number `0x0014`) enabling promiscuous frame reception at the driver level. No public source documents its behavior.

```bash
su -c "/data/local/tmp/iwpriv wlan0 set_sw_ctrl 1 0"
su -c "/data/local/tmp/iwpriv wlan0 set_sw_ctrl 2 0"
```

Capture used to confirm the behavior:

```bash
su -c "tcpdump -i wlan0 -e -v -c 20"
```

**Frame types observed** (not retained beyond confirming the finding):

- ARP, DNS, and mDNS frames from third-party devices on the network
- EAPOL 4-way handshake frames from other clients' association exchanges — this is the point at which it became clear the capture was not limited to own traffic
- Traffic sourced from multiple distinct MAC addresses not belonging to the research device

Link type: `EN10MB` (Ethernet) — frames are delivered as Ethernet rather than raw 802.11. This is a driver-layer capture, not a raw RF-layer capture: the driver is reassembling/de-encapsulating 802.11 frames into Ethernet format before handing them to the packet socket, which is consistent with a promiscuous mode implemented at the netdevice level rather than a true monitor-mode radiotap interface.

No sustained or bulk captures were run once third-party traffic was confirmed present. No credential-adjacent material from handshake frames was used, analyzed, or stored. The finding is that the ioctl exists and does this — not a demonstration of an attack against the handshake material.

---

## [5] Finding 3 — Hardware RF Monitor Mode (Raw 802.11 Statistics)

**CONFIRMED** — Hardware RX monitor mode unlocked — all-channel frame counting with RSSI confirmed.

The vendor factory test binary `/vendor/bin/wifitest` exposes a hardware RX test mode placing the chip in a pure receive state, disconnecting from any associated network and counting all 802.11 frames on the specified channel.

```bash
su -c "/vendor/bin/wifitest -r -c <channel> -b 0 -Q 1 -S <seconds>"
```

**Parameters:**

| Flag | Value | Meaning |
|---|---|---|
| -r | — | RX test mode — pure hardware receive |
| -c | 1-13 / 36-165 | Channel number (2.4GHz / 5GHz) |
| -b | 0-7 | Bandwidth: 0=20MHz, 1=40MHz, 2=80MHz, 3=160MHz, etc. |
| -Q | 1 | RX path 0 (2=RX1, 3=both — fails on this chip) |
| -S | integer | Test duration in seconds |

Observed output:

```
[ 0] (1)RX Total OK Count: 11 /(1)RX Total ERR Count: 1 / PER: 8 .. / Rx Total Count: 12 (1)RSSI0: -70
[ 1] (1)RX Total OK Count: 362 /(1)RX Total ERR Count: 93 / PER: 20 .. / Rx Total Count: 455 (1)RSSI0: -86
```

**Key observations:**

- Frames counted from all 802.11 devices on the channel — not limited to the associated network
- RSSI range observed: -70 to -96 dBm (nearby to distant devices)
- PER of 8–27% consistent with weak or distant signal sources
- Approximately 500 frames/second on a typical 2.4GHz channel
- WiFi association fully drops for the duration of the test — the chip is in exclusive RF-receive state, meaning this mode is not concurrent with normal connectivity

The `-Q 3` (both RX paths) parameter fails on this chip, indicating the connac2 RX-diversity path is either not wired up in this firmware build or gated behind a capability this test mode doesn't unlock.

---

## [6] Finding 4 — Hardware TX Frame Injection

**CONFIRMED** — TX injection fully unlocked — 100% packet delivery success rate confirmed.

Hardware-level frame transmission was demonstrated via `wifitest`'s TX mode. Injection was confirmed across multiple 802.11 PHY modes (11abg, 11n, 11ac, 11ax, 11be), multiple rates, and configurable frame lengths.

```bash
su -c "/vendor/bin/wifitest -t 0 -c 6 -b 0 -R 1 -s 0 -n 100 -l 1024 -p 10"
```

**Parameter reference:**

| Flag | Value | Meaning |
|---|---|---|
| -t | 0–4 | TX mode: 0=11abg, 1=11n, 2=11ac, 3=11ax, 4=11be |
| -R | 1–12 | Legacy rate: 1=1Mbps through 12=54Mbps |
| -s | 0 | Short preamble |
| -n | integer | Frame count (0 = continuous) |
| -l | integer | Frame length in bytes |
| -p | integer | TX power gain in dBm |
| -y | 1–3 | TX path: 1=Tx0, 2=Tx1, 3=both |

Observed output:

```
[0] Tx total/good count: 18/18
[1] Tx total/good count: 100/100
...
(success) stop Tx (Dbdc0)
```

**Result:** 100/100 frames transmitted successfully. Injection is evidenced by: (1) `wifitest -t` completing with zero dropped frames across all reported intervals; (2) Tx good count equaling Tx total count in every output line; (3) the explicit success confirmation in the final stop message. The chip supports injection across the full 802.11 generation stack from legacy OFDM through WiFi 7 (11be).

This is a delivery-count test against the chip's own reporting, not a test against a target device or network — the frames are counted by the transmitting chip's own TX-good counter, which reflects successful handoff to the PHY, not reception confirmation by any listener.

---

## [7] Finding 5 — Firmware Log Device Access

**CONFIRMED** — Firmware log device readable — baseband, RF calibration, and monitor strings extracted.

The kernel exposes a character device `/dev/fw_log_wifi` (major 477, owned by wifi:wifi) streaming live firmware log output.

```bash
su -c "cat /dev/fw_log_wifi > /sdcard/fw_log.txt &"
su -c "/vendor/bin/wifitest -r -c 6 -b 0 -Q 1 -S 3"
su -c "killall cat"
```

**Notable strings extracted:**

| Log Entry | Significance |
|---|---|
| `BB1_log : : 7E4 TOO SMALL!` | Baseband attempting to dump packets >2020 bytes — hardcoded buffer limit |
| `CAL: phyCalRfSxCal` | RF calibration running across multiple channels |
| `ANT: _halEpaAntSelSetHwInfo` | Antenna selection hardware event |
| `Channel scan: 2402-2472 MHz, 5180 MHz` | Full 2.4GHz band + 5GHz channel scanned |
| `IDLM monitor` | Monitor mode string present in production firmware binary |
| `Monitor Duration: %d unit = %d ms` | Monitor duration timer — confirms monitor mode code path exists in firmware |

**Full log device listing:**

| Device | Purpose |
|---|---|
| /dev/fw_log_wifi | WiFi firmware log |
| /dev/fw_log_ics | Integrated Connectivity Subsystem log |
| /dev/fw_log_wifimcu | WiFi MCU log |
| /dev/fw_log_bt | Bluetooth log |
| /dev/fw_log_btmcu | Bluetooth MCU log |
| /dev/fw_log_gps | GPS log |

The `BB1_log 7E4 TOO SMALL` message is the direct evidence for the buffer ceiling documented in the Summary table: `0x7E4` = 2020 decimal, and any packet whose baseband dump would exceed that many bytes is truncated/dropped at the logging layer rather than the capture layer, meaning the frame is received but not fully exposed via this path.

---

## [8] Finding 6 — Kernel Tracepoint Capture

**CONFIRMED** — 1913 kernel trace entries captured covering full WiFi packet lifecycle.

The kernel exposes a dedicated WiFi tracing instance at `/sys/kernel/tracing/instances/wifi/` with a `connsys_trace_event` tracepoint category.

```bash
su -c "echo 1 > /sys/kernel/tracing/instances/wifi/events/connsys_trace_event/enable"
su -c "echo 8192 > /sys/kernel/tracing/instances/wifi/buffer_size_kb"
su -c "echo 1 > /sys/kernel/tracing/instances/wifi/tracing_on"
su -c "cat /sys/kernel/tracing/instances/wifi/trace"
```

**Sample captured events** (from the research device's own connection/association activity):

```
net_dev_queue: dev=wlan0 skbaddr=... len=86 (TX queued)
netif_rx: dev=wlan0 skbaddr=... len=121 (RX received)
netif_receive_skb: dev=wlan0 skbaddr=... len=121 (RX delivered to stack)
net_dev_xmit: dev=wlan0 skbaddr=... len=141 rc=0 (TX transmitted)
rdev_connect: phy0, ssid: Amir, wpa versions: 2 (Association)
rdev_add_key: phy0, key_index: 0, pairwise: true (WPA key install)
```

**Result:** 1913 trace entries captured in a single session, covering TX queue, RX delivery, WPA association, and key installation events — complete kernel-level visibility into the WiFi packet lifecycle of the research device itself. The `rdev_add_key` event confirms this tracepoint category sits above the crypto layer (post key-derivation, pre key-installation into hardware), which is useful context if this trace path is used alongside Finding 2's capture to correlate handshake timing with visible EAPOL frames.

---

## [9] iwpriv Private Ioctl Reference

Complete private ioctl list as enumerated via strace and iwpriv on wlan0:

| Command | Ioctl # | Set | Get | Notes |
|---|---|---|---|---|
| driver | 8BEF | 2000 char | 2047 char | General driver command interface |
| AP_SET_CFG | 8BF7 | 256 char | 1024 char | AP configuration |
| AP_GET_STA_LIST | 8BF3 | 1024 char | 1024 char | AP station list |
| AP_SET_MAC_FLTR | 8BF5 | 256 char | 1024 char | MAC filter |
| AP_STA_DISASSOC | 8BF9 | 256 char | 1024 char | Force station disassociation |
| AP_SET_NSS | 8BFB | 256 char | 1024 char | Spatial stream config |
| AP_SET_BW | 8BFD | 256 char | 1024 char | Bandwidth config |
| set_tcp_csum | 0003 | 1 int | — | — |
| set_power_mode | 0006 | 1 int | — | — |
| get_power_mode | 0006 | — | 1 int | — |
| set_wmm_ps | 0007 | 3 int | — | — |
| set_test_mode | 0011 | 1 int | — | — |
| set_test_cmd | 0012 | 2 int | — | — |
| get_test_result | 0012 | 2 int | 1 int | — |
| set | 001D | 2000 char | — | — |
| **set_sw_ctrl** | **0014** | **2 int** | **—** | **KEY: enables promiscuous mode** |
| get_sw_ctrl | 0014 | 1 int | 1 int | — |
| set_oid | 000F | 256 | — | **WARNING: caused kernel panic — avoid** |
| get_oid | 000F | — | 256 | — |
| set_band | 001A | 1 int | — | — |
| get_band | 001A | — | 1 int | — |
| get_ch_list | 0018 | — | 50 int | — |
| get_mem | 001B | 2 int | 1 int | — |
| set_p2p_mode | 001C | 2 int | — | — |
| set_met_prof | 0021 | 2 int | — | — |
| set_ser | 0025 | 1 int | — | Possible sniffer enable path |
| connStatus | 002A | — | 2000 char | — |
| show_Channel | 002E | — | 1 int | — |
| set_mdvt | 002F | 2 int | — | FAILED: not supported on this chip |

**Discovered ioctl numbers via strace:**

| Ioctl Number | Function |
|---|---|
| 0x8BE0 | SIOCIWFIRSTPRIV — set operations |
| 0x8BE1 | Get operations |
| 0x8BE5 | connStatus |
| 0x8BED | Alternate ioctl endpoint (many sub-commands) |
| 0x8BEE | FAILED — operation not supported |

Note the numeric collision between `set_sw_ctrl`/`get_sw_ctrl` and `set_oid`/`get_oid` families is not actually a collision — `0x0014` and `0x000F` are distinct base command IDs; `iwpriv` resolves the same ioctl number (`SIOCIWFIRSTPRIV`-relative) to different handlers based on the sub-command index encoded in the char buffer, which is why `set_oid`'s raw-register-write semantics are far more dangerous than `set_sw_ctrl`'s bitmask toggle despite living in adjacent command space.

---

## [10] Vendor Test Tool Inventory

| Binary | Path | Purpose |
|---|---|---|
| wifitest | /vendor/bin/wifitest | Hardware RX/TX test, NVRAM R/W, FFT — primary research tool |
| wlan_assistant | /vendor/bin/wlan_assistant | WiFi file monitor daemon |
| wifi_dump | /vendor/bin/wifi_dump | Connects to NETLINK socket for packet dump |
| wmt_launcher | /vendor/bin/wmt_launcher | WMT firmware loader (SDIO/UART modes) |
| wmt_loader | /vendor/bin/wmt_loader | Firmware patch loader |

---

## [11] Key Files and Devices

| Path | Purpose |
|---|---|
| /mnt/vendor/nvdata/APCFG/APRDEB/WIFI | WiFi calibration/firmware config — patched at offset 0x02e0 |
| /vendor/firmware/wifi.cfg | WiFi configuration parameters |
| /vendor/firmware/soc7_0_ram_mcu_1_1_hdr.bin | MCU firmware — contains "IDLM monitor" string |
| /vendor/firmware/soc7_0_ram_bt_1_1_hdr.bin | Bluetooth firmware |
| /dev/wmtWifi | WMT char device (major 479) |
| /dev/fw_log_wifi | WiFi firmware log stream (major 477) |
| /sys/kernel/tracing/instances/wifi/ | WiFi kernel tracing instance |

---

## [12] Technical Observations

1. **`set_oid` is dangerous** — Issuing `set_oid` (ioctl `0x8BEF`, sub-command `000F`) with an unknown OID caused a full kernel panic and device reboot. Raw OID writes should only be attempted with exact knowledge of the target register — this is consistent with `set_oid` being a thin passthrough to the firmware's internal OID-based config interface with no bounds/validity checking exposed at the ioctl layer.
2. **Firmware patch persists across reboots** — The WIFI bin patch at offset `0x02e0` causes the chip to boot directly into test mode. Verified by `wifitest -O` reporting "Already in test mode" without manual intervention after reboot.
3. **Hardware RX test is exclusive** — `wifitest -r` fully disconnects WiFi for the test duration. The chip operates in a pure hardware RF-receive state with no concurrent association, meaning this mode cannot be run passively alongside normal connectivity — it's a dedicated diagnostic state, not a background capture mode.
4. **Firmware buffer limitation** — The BB1_log subsystem has a hardcoded `0x7E4` (2020-byte) buffer. Packets exceeding this size produce a "TOO SMALL" log entry, preventing raw frame dump of large packets via this path. This caps the firmware-log route as a capability, not the chip's actual RF receive capability — the frame is received and processed for stats (Finding 3), just not fully exposed through the log device.
5. **Vendor tooling bypasses the Linux wireless stack** — `wifitest`, `wlan_assistant`, and `wifi_dump` provide direct hardware register access that `cfg80211`/`nl80211` do not expose, making them the primary research surface for this chip family. Any audit of connac2-based devices that only inspects the nl80211 interface list will miss this surface entirely.
6. **The promiscuous-mode finding was accidental, not designed** — worth restating as a technical observation, not just an ethics note: `set_sw_ctrl`'s effect was not known in advance. That production firmware exposes this with no explicit warning or documentation is itself part of the finding — it implies the ioctl's promiscuous-capture behavior may be an artifact of a debug/manufacturing test path left reachable in shipping firmware, rather than a deliberately designed and gated user-facing feature.

---

## [13] Summary of Capabilities Unlocked

| Capability | Status | Evidence |
|---|---|---|
| Promiscuous Mode | UNLOCKED (accidental) | `set_sw_ctrl` ioctl + tcpdump capture of third-party ARP/DNS/EAPOL frames — not the intended outcome of the test |
| Hardware RF Monitor | UNLOCKED | `wifitest -r`: per-interval frame counts, RSSI, PER across all 802.11 devices on channel |
| Hardware TX Injection | UNLOCKED | `wifitest -t`: 100/100 frames, 100% good count, (success) stop confirmation — self-reported by transmitting chip, not a third-party target |
| Firmware Log Access | UNLOCKED | `/dev/fw_log_wifi` streaming: BB1, RF cal, antenna, channel scan, monitor strings |
| Kernel Packet Trace | UNLOCKED | 1913 connsys_trace_event entries: TX/RX lifecycle, WPA association, key install (research device's own traffic) |
| Raw 802.11 Frame Dump | PARTIAL | BB1_log buffer hardcoded at 0x7E4 — too small for full packet capture via firmware path |
| EAPOL Frame Visibility | UNLOCKED (accidental) | 4-way WPA handshake frames observed passing through promiscuous capture from third-party clients — not retained or analyzed |
| Boot-Persistent Config | UNLOCKED | NVRAM patch at 0x02e0 survives reboot — chip enters test mode autonomously on boot |

All capabilities documented in this report were demonstrated through direct hardware interaction on the research device. The MediaTek MT6639 (connac2) chipset exposes a substantially richer set of RF capabilities than its `cfg80211` advertisement suggests, accessible via vendor factory tooling and proprietary driver ioctls present in production firmware. The promiscuous-capture finding in particular was an accidental discovery, not a planned or repeated capture of third-party traffic, and is documented here for accuracy rather than as a demonstrated technique.
