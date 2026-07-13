# Key Files and Devices

| Path | Purpose |
|---|---|
| `/mnt/vendor/nvdata/APCFG/APRDEB/WIFI` | WiFi calibration/firmware config — patched at offset `0x02e0` |
| `/vendor/firmware/wifi.cfg` | WiFi configuration parameters |
| `/vendor/firmware/soc7_0_ram_mcu_1_1_hdr.bin` | MCU firmware — contains `IDLM monitor` string |
| `/vendor/firmware/soc7_0_ram_bt_1_1_hdr.bin` | Bluetooth firmware |
| `/dev/wmtWifi` | WMT char device (major 479) |
| `/dev/fw_log_wifi` | WiFi firmware log stream (major 477) |
| `/sys/kernel/tracing/instances/wifi/` | WiFi kernel tracing instance |

See [Finding 1](../findings/01_nvram_patch.md) for the NVRAM patch procedure and [Finding 5](../findings/05_fw_log.md) for firmware log usage.
