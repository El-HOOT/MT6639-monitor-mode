# Finding 6 — Kernel Packet Trace (`connsys_trace_event`)

**Status:** CONFIRMED  
**Entries captured:** 1913  
**Path:** `/sys/kernel/tracing/instances/wifi/`

---

```bash
su -c "echo 1 > /sys/kernel/tracing/instances/wifi/events/connsys_trace_event/enable"
su -c "echo 8192 > /sys/kernel/tracing/instances/wifi/buffer_size_kb"
su -c "echo 1 > /sys/kernel/tracing/instances/wifi/tracing_on"
su -c "cat /sys/kernel/tracing/instances/wifi/trace"
```

**Sample events:**

```
net_dev_queue: dev=wlan0 skbaddr=... len=86
netif_rx: dev=wlan0 skbaddr=... len=121
netif_receive_skb: dev=wlan0 skbaddr=... len=121
net_dev_xmit: dev=wlan0 skbaddr=... len=141 rc=0
rdev_connect: phy0, ssid: Amir, wpa versions: 2
rdev_add_key: phy0, key_index: 0, pairwise: true
```

Covers TX queue, RX delivery, WPA association, and key installation — full kernel-level WiFi packet lifecycle. All traffic captured was the research device's own.
