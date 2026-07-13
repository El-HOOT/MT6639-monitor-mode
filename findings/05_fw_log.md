# Finding 5 — Firmware Log Device (`/dev/fw_log_wifi`)

**Status:** CONFIRMED  
**Device:** `/dev/fw_log_wifi` (major 477, owned by wifi:wifi)

---

```bash
su -c "cat /dev/fw_log_wifi > /sdcard/fw_log.txt &"
su -c "/vendor/bin/wifitest -r -c 6 -b 0 -Q 1 -S 3"
su -c "killall cat"
```

**Notable strings extracted:**

| Log Entry | Significance |
|---|---|
| `BB1_log : : 7E4 TOO SMALL!` | Baseband buffer limit — blocks raw frame dump of packets >2020 bytes |
| `CAL: phyCalRfSxCal` | RF calibration across channels |
| `ANT: _halEpaAntSelSetHwInfo` | Antenna selection event |
| `Channel scan: 2402-2472 MHz, 5180 MHz` | Full 2.4GHz + 5GHz scan |
| `IDLM monitor` | Monitor mode string in production firmware |
| `Monitor Duration: %d unit = %d ms` | Monitor duration timer — code path exists in firmware |

**Full log device list:**

| Device | Purpose |
|---|---|
| `/dev/fw_log_wifi` | WiFi firmware log |
| `/dev/fw_log_ics` | Integrated Connectivity Subsystem log |
| `/dev/fw_log_wifimcu` | WiFi MCU log |
| `/dev/fw_log_bt` | Bluetooth log |
| `/dev/fw_log_btmcu` | Bluetooth MCU log |
| `/dev/fw_log_gps` | GPS log |
