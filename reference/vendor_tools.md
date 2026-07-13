# Vendor Test Tool Inventory

| Binary | Path | Purpose |
|---|---|---|
| wifitest | `/vendor/bin/wifitest` | Hardware RX/TX test, NVRAM R/W, FFT — primary research tool |
| wlan_assistant | `/vendor/bin/wlan_assistant` | WiFi file monitor daemon |
| wifi_dump | `/vendor/bin/wifi_dump` | Connects to NETLINK socket for packet dump |
| wmt_launcher | `/vendor/bin/wmt_launcher` | WMT firmware loader (SDIO/UART modes) |
| wmt_loader | `/vendor/bin/wmt_loader` | Firmware patch loader |

`wifitest` is the primary surface used across [Finding 3](../findings/03_rf_monitor.md), [Finding 4](../findings/04_tx_injection.md), and [Finding 1](../findings/01_nvram_patch.md) (via `-O` test-mode check).
