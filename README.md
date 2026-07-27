# LGS-Test-Tool

Web-based test tool for **LGS R5.0 locker modules**: fires Modbus **RTU** (COM port) or
Modbus **TCP** (via the LGS gateway) commands from a browser UI. Built with
[NiceGUI](https://nicegui.io) + [pymodbus](https://github.com/pymodbus-dev/pymodbus);
runs natively on Windows or in Docker.

Four tabs:

| Tab | What it does |
|---|---|
| **Control** | Preset 1-8 buttons (light / light+display / unlock / unlock+display), OLED number + display power, Identify / All Off / latch triggers with a live 2.2 s cooldown chip, generic register & coil read/write |
| **Monitor** | 0.5-2 s poll of device info, uptime, boot counter, health bits, reset cause (sticky — the register is clear-on-read), temperatures (0x8000 → SENSOR FAULT), latch state, statistics |
| **Auto Test** | The full R5.0 sweep (READ → WRITE → VALIDATE → PRESET → DISPLAY → LED → optional LATCH) with live PASS/FAIL table and CSV export — a GUI port of `LGS-Standard-Module/tools/test_modbus_rtu.py` |
| **Danger** | Factory reset (type-the-ID + double confirm), save-to-EEPROM, software reset, clear statistics — with post-reboot probes |

A transaction log pane (all sources, raw TX/RX hex, CSV export) sits under every tab.

Safety is enforced in the worker, not just the UI: OTA coils 505-508 are always refused
(use `ota_sender.py`), danger coils only fire through the Danger tab, latch coils are
cooldown-gated (≥2.2 s), and the whole app funnels every transaction through one queue —
one Modbus client, one COM port / one TCP socket (the gateway accepts a single client).

## Hardware setups

1. **USB-RS485 dongle** → COM port, RTU 9600 8N1 (fixed framing, baud per module config).
2. **Arduino Opta as USB-RS485 bridge** (repo `LGS-Gateway-Arduino-Opta`, `USB_BRIDGE_ON_BOOT 1`):
   plug the Opta's USB-C, blue USER LED on = bridge active. The COM port is auto-detected
   and labeled. PC-side baud is ignored (USB CDC); the RS485 side always runs at 9600.
3. **Opta as Modbus TCP gateway** (`USB_BRIDGE_ON_BOOT 0` + LAN cable — `Ethernet.begin()`
   blocks without link): TCP `192.168.0.178:502`, **one client at a time**.

Module addressing: grid slave ID = `row*10 + col` (rows 1-6, cols 1-4 → 11..64), factory
default **247**, ID 246 reserved (SET_ID), 0 = broadcast (not used by this tool).
Command reference: `LGS-Standard-Module/doc/LGS-Control-Table.md`.

## Run (native, Windows)

```powershell
& "C:\Users\mteer\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m app.main
```

Open http://localhost:8080 (a browser window opens automatically; set `LGS_TT_NO_BROWSER=1`
to suppress). Config (last port/IP/ID) persists in `data/config.json`; sweep and log CSVs
land in `data/exports/`.

> OneDrive note: `.venv/` is gitignored but OneDrive still syncs it — consider excluding
> the folder from sync ("Choose folders") if it causes churn.

## Portable Windows build (one-click install)

The easiest way to put the tool on another Windows PC — a single `.exe`, no Python,
no Docker, and COM ports work natively (which Docker on Windows cannot do):

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

This produces `dist\LGS-Test-Tool-v<version>.exe` (PyInstaller one-file via
`nicegui-pack`; the version comes from `app/version.py`, e.g.
`LGS-Test-Tool-v1.1.0.exe`). Copy that file anywhere, double-click: a console window
opens, the browser opens at http://localhost:8080, and a `data\` folder (config + CSV
exports) is created next to the exe. Close the console window to stop the server.

Notes:
- First launch is slower (~5-30 s) — the one-file exe unpacks itself to temp and
  Windows Defender scans it once.
- Unsigned exe: Windows SmartScreen may warn on first run — choose
  "More info" → "Run anyway".
- Windows Firewall prompt: localhost use works either way; click "Allow" only if
  other PCs on the LAN should reach the page.
- Rebuild after any code change; the exe is a frozen snapshot.

## Run (Docker — TCP only)

```bash
docker build -t lgs-test-tool .
docker run -d -p 8080:8080 -v lgs_data:/app/data --name lgs-test-tool lgs-test-tool
```

Windows Docker cannot pass COM ports into containers, so containerized deployments use the
TCP transport (the RTU controls stay visible but list no ports). On a Linux host you could
add `--device=/dev/ttyUSB0` and use RTU as well.

## Development notes

- `app/lgs_map.py` mirrors the firmware's `src/svc/modbus_map.h` — one row per address,
  wire-contract asserts at import, `python -m app.lgs_map` dumps the table.
- All Modbus I/O runs on the single worker thread in `app/modbus_worker.py`; UI code never
  touches pymodbus. `reload=False` is mandatory (a reloader would spawn a second worker).
- Addresses are raw wire addresses — **no ±1 PLC offset anywhere**.
- pymodbus ≥ 3.9 required (`device_id=` kwarg); tested with the versions pinned in
  `requirements.txt`.

## Publishing to GitHub (when ready)

```powershell
gh repo create M-TRCH/LGS-Test-Tool --private --source=. --remote=origin --push
```

or manually: `git remote add origin https://github.com/M-TRCH/LGS-Test-Tool.git` then
`git push -u origin main`.

---

## สรุปภาษาไทย

เครื่องมือทดสอบโมดูล LGS R5.0 ผ่านเว็บเบราว์เซอร์ — ยิงคำสั่ง Modbus ได้ทั้งทาง **RTU
(COM port** ผ่าน dongle หรือ Opta USB-RS485 bridge**)** และ **Modbus TCP** (ผ่าน Opta
gateway ที่ `192.168.0.178:502` ซึ่งรับทีละ 1 client) มี 4 แท็บ: **Control**
(ปุ่ม preset 1-8 / latch / display + อ่านเขียน register อิสระ), **Monitor** (สถานะเครื่อง
อุณหภูมิ health ทุก 1 วิ), **Auto Test** (ชุดทดสอบอัตโนมัติพร้อมสรุป PASS/FAIL + CSV),
**Danger** (factory reset / save EEPROM / soft reset / clear stats — ต้องยืนยันสองชั้น)

ระบบกันพลาด: coil OTA (505-508) ถูกปฏิเสธเสมอ, coil อันตราย (500-504, 510) ยิงได้เฉพาะ
แท็บ Danger, latch ติด cooldown 2.2 วินาที ตาม spec ของ firmware

วิธีรัน: สร้าง venv + `pip install -r requirements.txt` แล้ว
`.venv\Scripts\python -m app.main` เปิด http://localhost:8080 — หรือรันใน Docker
(ใช้ได้เฉพาะ TCP เพราะ Windows ส่ง COM port เข้า container ไม่ได้)

**ติดตั้งเครื่องอื่นแบบคลิกเดียว:** รัน `build_exe.ps1` จะได้
`dist\LGS-Test-Tool-v<เวอร์ชัน>.exe` ไฟล์เดียว (เลขเวอร์ชันอยู่ในชื่อไฟล์ เช่น
`LGS-Test-Tool-v1.1.0.exe`) — ก๊อปปี้ไปเครื่องไหนก็ได้ ดับเบิลคลิกใช้งานเลย (ไม่ต้องมี Python และใช้
COM port ได้ปกติ) ปิดหน้าต่าง console เพื่อหยุดโปรแกรม — ครั้งแรก Windows SmartScreen
อาจเตือน ให้กด "More info" → "Run anyway"
