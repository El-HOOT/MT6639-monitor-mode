# Finding 4 — Hardware TX Frame Injection (`wifitest -t`)

**Status:** CONFIRMED  
**Tool:** `/vendor/bin/wifitest`  
**Result:** 100/100 frames, 100% good count

---

```bash
su -c "/vendor/bin/wifitest -t 0 -c 6 -b 0 -R 1 -s 0 -n 100 -l 1024 -p 10"
```

| Flag | Value | Meaning |
|---|---|---|
| `-t` | 0–4 | TX mode: 0=11abg, 1=11n, 2=11ac, 3=11ax, 4=11be |
| `-R` | 1–12 | Legacy rate: 1=1Mbps → 12=54Mbps |
| `-s` | 0 | Short preamble |
| `-n` | integer | Frame count (0 = continuous) |
| `-l` | integer | Frame length in bytes |
| `-p` | integer | TX power gain in dBm |
| `-y` | 1–3 | TX path: 1=Tx0, 2=Tx1, 3=both |

**Sample output:**

```
[0] Tx total/good count: 18/18
[1] Tx total/good count: 100/100
...
(success) stop Tx (Dbdc0)
```

**Notes:**

- Injection confirmed across full 802.11 stack: 11abg through 11be (WiFi 7)
- Delivery count is self-reported by the transmitting chip — no target device involved
- Continuous injection possible with `-n 0`
