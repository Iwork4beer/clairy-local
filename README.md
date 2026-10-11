# Clairy Natural Air Purifier de-cloud and Home Assistant integration

If you own one, you probably know the story. I love my Clairy — it's a beautiful SMART pot, or at least it was supposed to be. The app never really fully worked, ever, and then the company decided to drop support altogether. We do not like that.

I couldn't find any online community of Clairy enthusiasts, so I might as well start here.

After moving mine to my office, I had a brainwave and decided to give Codex a shot at modifying the app.

One evening later, I present to you: a local-only, de-clouded Natural Air Purifier.

No cloud required, and it also integrates easily with Home Assistant.

The pot is smart again.

<img width="720" height="1600" alt="Working Android app" src="https://github.com/user-attachments/assets/cf385e6a-6a18-4762-ba61-532bb872bc79" />
<img width="720" height="402" alt="Home Assistant Card" src="https://github.com/user-attachments/assets/59d96c6c-210d-4794-ba37-bee28b4c22b6" />


# Clairy Local

Unofficial community project for keeping first-generation **Clairy** natural air purifiers useful after the original cloud service became unavailable.

The goal is local-only operation: provisioning a Clairy onto Wi-Fi, reading its sensors over the LAN, preserving the original Android UI where practical, and integrating the device with Home Assistant without depending on Clairy's former cloud infrastructure.

## Project status

This project is early, but the local Android modification and LAN sensor reading have been tested on original Clairy hardware.

Current work includes:

- documentation of the Clairy local UDP protocol;
- a standalone Python reader for local sensor data;
- a Home Assistant custom integration for temperature, humidity and Clairy's air-quality reading;
- tooling to patch a user-supplied copy of the original Android APK for local-only operation.

## Android application

**The original Clairy APK and patched APKs are not distributed by this repository.**

The Android tooling is intended to operate on an original APK supplied by the device owner. This keeps Clairy's copyrighted application, artwork and other assets out of this repository.

## Local sensor data

The first-generation Clairy communicates locally over IPv4 UDP port `6666` and multicast group `239.0.0.1`. Current readings observed in the application protocol include temperature, relative humidity and Clairy's unitless air-quality/IAQ value.

The air-quality value should not be represented as a VOC concentration: the application protocol exposes Clairy's calculated quality score, not a raw VOC concentration in ppb, ppm or mg/m³.

## Disclaimer

Clairy Local is an independent, unofficial interoperability and preservation project. It is not affiliated with, sponsored by, or endorsed by Clairy or Laboratori Fabrici S.r.l.

Clairy and associated names and trademarks belong to their respective owners. The MIT license in this repository applies only to code and documentation contributed to this project; it does not grant rights to the original Clairy software, firmware, artwork, trademarks or other third-party material.

## License

Original code and documentation in this repository are released under the [MIT License](LICENSE), unless a file states otherwise.
