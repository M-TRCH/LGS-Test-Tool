# Bundled binaries

Firmware images shipped **inside** the tool, because the jobs they do happen
on site where there is no PlatformIO, no Arduino IDE and often no network.

Everything here is a **released** image, copied byte for byte from its GitHub
release asset. A work-in-progress build in this folder is a build somebody
will flash into a cabinet by accident. `app/firmware_bundle.py` records the
SHA-256 of each one and refuses to load an image that no longer matches, and
`build_exe.ps1` checks the same hashes before packaging.

To add a newer release: copy the asset in, add an entry to
`app/firmware_bundle.py` (newest first — the first entry of a kind is the one
its tab offers), and add the hash to `build_exe.ps1`.

## gateway_opta_v1.10.0.bin

`LGS-Gateway-Opta-v1.10.0.bin` from LGS-Gateway-Arduino-Opta release v1.10.0.
Offered by the Gateway tab for UPDATE FIRMWARE, and as the firmware restored
at the end of PREPARE A NEW OPTA. Upgrading from ANY earlier version wipes
the stored settings (schema change) — export the config first, flash, import.

## module_g070_v3.2.0_factory.bin

`firmware_stm32g070_v3.2.0_factory_2026-08-06.bin` from LGS-Standard-Module
release v3.2.0 — bootloader + application, written over ST-Link. This is the
one that carries the commissioning block the New Module tab patches an ID
into; the OTA image has no such block and the tab rejects it on sight.

## module_g070_v3.2.0_ota.bin

`firmware_stm32g070_v3.2.0_2026-08-06.bin` from the same release —
application only, linked at 0x1000, for the Firmware (OTA) tab. Sending a
factory image over the air would write a bootloader into the application
slot, so the two are separate kinds and each tab only ever sees its own.

## qspiformat_opta.bin

Arduino's `QSPIFormat` example (mbed core, `libraries/STM32H747_System/
examples/QSPIFormat`), built for `board = opta`, unmodified.

A factory-fresh Opta has no partition table on its QSPI flash, so the gateway
firmware finds no KVStore and reports `cfg.store=unavailable` /
`cfg.why=kvstore partition 3 missing` — settings cannot be saved at all. This
image creates the partitions once: WiFi 1 MB, OTA 5 MB, **KVStore 1 MB**
(the one the gateway needs), user data 7 MB.

The gateway firmware deliberately never creates them itself: the same QSPI
holds the WiFi firmware and the OTA area, and a partition table this tool
wrote by guessing would be a good way to destroy a working board.

Rebuild it the same way if the core is ever updated:

    pio project init --board opta            # in an empty directory
    cp <core>/libraries/STM32H747_System/examples/QSPIFormat/*.ino src/main.ino
    cp <core>/libraries/STM32H747_System/examples/QSPIFormat/*.h  src/
    pio run

Keep the build path short — the mbed core's object paths overflow Windows'
260-character limit from anywhere deep.
