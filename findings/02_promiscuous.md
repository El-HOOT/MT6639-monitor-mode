# Finding 2 — Promiscuous Mode via `set_sw_ctrl`

**Status:** CONFIRMED (accidental discovery)  
**Ioctl:** `set_sw_ctrl` (`0x0014`)  
**Capture layer:** Ethernet (EN10MB) — not raw 802.11

---

`set_sw_ctrl` is a private ioctl with no public documentation. Testing it to understand its behavior produced promiscuous-mode capture as an unintended side effect.

```bash
su -c "/data/local/tmp/iwpriv wlan0 set_sw_ctrl 1 0"
su -c "/data/local/tmp/iwpriv wlan0 set_sw_ctrl 2 0"
su -c "tcpdump -i wlan0 -e -v -c 20"
```

**Frame types observed:**

- ARP, DNS, mDNS from third-party devices
- EAPOL 4-way handshake frames from other clients' association exchanges
- Traffic from multiple MACs not belonging to the research device

**Notes:**

- Frames arrive as Ethernet, not raw 802.11 — this is a driver-layer capture
- Capture was stopped once third-party traffic was confirmed visible
- No third-party traffic was retained or analyzed beyond confirming the finding

See [DISCLAIMER.md](../DISCLAIMER.md).
