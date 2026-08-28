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

## gateway_opta_v1.12.2.bin

`gateway_opta_v1.12.2.bin` from LGS-Gateway-Arduino-Opta release v1.12.2.
Offered by the Gateway tab for UPDATE FIRMWARE and restored at the end of
PREPARE A NEW OPTA. Schema unchanged from v1.12.0 — updating from v1.12.0
or v1.12.1 keeps the stored settings.

## module_g070_v3.4.0_factory.bin

`firmware_stm32g070_v3.4.0_factory_2026-08-28.bin` from LGS-Standard-Module
release v3.4.0 — bootloader + application, written over ST-Link. Carries the
commissioning block the New Module tab patches an ID into; the OTA image has
no such block and the tab rejects it on sight.

## module_g070_v3.4.0_ota.bin

`firmware_stm32g070_v3.4.0_2026-08-28.bin` from LGS-Standard-Module release
v3.4.0 — the application alone, streamed over the bus by the Firmware tab.
Display renders 0-999 (reg 60); folds in the v3.3.1/v3.3.2 hardening.

## gateway_opta_v1.12.0.bin

Previous gateway release, kept for rollback. Upgrading from any version
BEFORE v1.12.0 wipes the stored settings (schema change) — export first.

## module_g070_v3.3.0_factory.bin / module_g070_v3.3.0_ota.bin

Previous module release, kept for rollback. OTA between v3.3.0 and v3.4.0
is safe in both directions (no schema change).

## qspiformat_opta.bin

Arduino's QSPIFormat sketch, needed once when preparing a factory-fresh
Opta whose QSPI has never been partitioned.
