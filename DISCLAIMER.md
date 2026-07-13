# Disclaimer

This research was performed on my own device using root access I control.

## What happened with promiscuous mode

Running `set_sw_ctrl` to probe an undocumented ioctl produced promiscuous-mode capture as an unintended side effect. I did not know it would do that before running it. When it became clear that third-party frames — including EAPOL handshakes from other clients — were passing through the interface, I stopped. No third-party traffic was retained, analyzed, or acted on beyond confirming the behavior exists.

This is documented as-is, not reframed as a controlled capture on "my own network." That would be inaccurate.

## Scope

- All testing was on hardware I own
- No third-party systems were targeted
- TX injection (`wifitest -t`) was a self-reported delivery count from the transmitting chip — no target device was on the receiving end
- Kernel trace captured the research device's own traffic only

## MediaTek

I have not filed anything with MediaTek. If that happens, it will be a separate formal write-up — not this archive.

## This document

This is a research archive. It is not a disclosure document, not a tutorial, and not an endorsement of using these capabilities against networks or devices you don't own.
