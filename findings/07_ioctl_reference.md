# Finding 7 — iwpriv Private Ioctl Reference

Enumerated via `strace` and `iwpriv` on `wlan0`.

---

## Private Ioctls

| Command | Ioctl # | Set | Get | Notes |
|---|---|---|---|---|
| driver | 8BEF | 2000 char | 2047 char | General driver command interface |
| AP_SET_CFG | 8BF7 | 256 char | 1024 char | AP configuration |
| AP_GET_STA_LIST | 8BF3 | 1024 char | 1024 char | AP station list |
| AP_SET_MAC_FLTR | 8BF5 | 256 char | 1024 char | MAC filter |
| AP_STA_DISASSOC | 8BF9 | 256 char | 1024 char | Force station disassociation |
| AP_SET_NSS | 8BFB | 256 char | 1024 char | Spatial stream config |
| AP_SET_BW | 8BFD | 256 char | 1024 char | Bandwidth config |
| set_tcp_csum | 0003 | 1 int | — | |
| set_power_mode | 0006 | 1 int | — | |
| get_power_mode | 0006 | — | 1 int | |
| set_wmm_ps | 0007 | 3 int | — | |
| set_test_mode | 0011 | 1 int | — | |
| set_test_cmd | 0012 | 2 int | — | |
| get_test_result | 0012 | 2 int | 1 int | |
| set | 001D | 2000 char | — | |
| **set_sw_ctrl** | **0014** | **2 int** | **—** | **Enables promiscuous mode — see [02_promiscuous.md](02_promiscuous.md)** |
| get_sw_ctrl | 0014 | 1 int | 1 int | |
| **set_oid** | **000F** | **256** | **—** | **⚠️ CAUSES KERNEL PANIC — do not use with unknown OIDs** |
| get_oid | 000F | — | 256 | |
| set_band | 001A | 1 int | — | |
| get_band | 001A | — | 1 int | |
| get_ch_list | 0018 | — | 50 int | |
| get_mem | 001B | 2 int | 1 int | |
| set_p2p_mode | 001C | 2 int | — | |
| set_met_prof | 0021 | 2 int | — | |
| set_ser | 0025 | 1 int | — | Possible sniffer enable path |
| connStatus | 002A | — | 2000 char | |
| show_Channel | 002E | — | 1 int | |
| set_mdvt | 002F | 2 int | — | FAILED — not supported on this chip |

---

## Ioctl Numbers (via strace)

| Ioctl Number | Function |
|---|---|
| 0x8BE0 | SIOCIWFIRSTPRIV — set operations |
| 0x8BE1 | Get operations |
| 0x8BE5 | connStatus |
| 0x8BED | Alternate endpoint (many sub-commands) |
| 0x8BEE | FAILED — operation not supported |
