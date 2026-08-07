# Bundled binaries

Firmware images shipped **inside** the tool, because the jobs they do happen
on site where there is no PlatformIO, no Arduino IDE and often no network.

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
