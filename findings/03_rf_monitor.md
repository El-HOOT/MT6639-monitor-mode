# Finding 3 — Hardware RF Monitor Mode (`wifitest -r`)

**Status:** CONFIRMED  
**Tool:** `/vendor/bin/wifitest`  
**Effect:** Full WiFi disconnection — chip enters exclusive RF-receive state

---

```bash
su -c "/vendor/bin/wifitest -r -c <channel> -b 0 -Q 1 -S <seconds>"
```

| Flag | Value | Meaning |
|---|---|---|
| `-r` | — | RX test mode |
| `-c` | 1–13 / 36–165 | Channel (2.4GHz / 5GHz) |
| `-b` | 0–7 | Bandwidth: 0=20MHz, 1=40MHz, 2=80MHz, 3=160MHz |
| `-Q` | 1 | RX path 0 (2=RX1, 3=both — fails on this chip) |
| `-S` | integer | Duration in seconds |

**Sample output:**

```
[ 0] (1)RX Total OK Count: 11 /(1)RX Total ERR Count: 1 / PER: 8 .. / Rx Total Count: 12 (1)RSSI0: -70
[ 1] (1)RX Total OK Count: 362 /(1)RX Total ERR Count: 93 / PER: 20 .. / Rx Total Count: 455 (1)RSSI0: -86
```

**Observations:**

- Counts frames from all 802.11 devices on the channel — not filtered to associated network
- RSSI observed: -70 to -96 dBm
- ~500 frames/second on a typical 2.4GHz channel
- WiFi association is fully dropped for the test duration
