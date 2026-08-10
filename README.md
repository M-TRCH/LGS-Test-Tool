# LGS-Test-Tool

Web-based test tool for **LGS R5.0 locker modules**: fires Modbus **RTU** (COM port) or
Modbus **TCP** (via the LGS gateway) commands from a browser UI. Built with
[NiceGUI](https://nicegui.io) + [pymodbus](https://github.com/pymodbus-dev/pymodbus);
runs natively on Windows or in Docker.

Tabs:

| Tab | What it does |
|---|---|
| **Control** | Preset 1-8 buttons (light / light+display / unlock / unlock+display), OLED number + display power, Identify / All Off / latch triggers with a live 2.2 s cooldown chip, generic register & coil read/write |
| **Monitor** | 0.5-2 s poll of device info, uptime, boot counter, health bits, reset cause (sticky — the register is clear-on-read), temperatures (0x8000 → SENSOR FAULT), latch state, UID, input current, confirm-button counter, statistics |
| **Installation Check** | **Many modules, few commands.** Pick a cabinet type (LGS 80 / 64 / 40, SMT), cells on the 10×8 map, or the last scan result, then send one command per module — light, or light + the slot's number, optionally upgraded to throw the latch. Every cell turns green or red. Also holds the **Pick walkthrough**: a batch of slots lights together, someone picks them in any order, and each light goes out as its button is pressed — optionally not until the drawer is closed again. CSV export |
| **Firmware (OTA)** | Streams a module image over the bus, and surveys the **whole cabinet's firmware versions** — every slot coloured by the version it reports, with each version group clickable to become the update targets |
| **New Module** | Flashes a blank module over ST-Link and gives it its Modbus ID in one step, single or continuous |
| **Gateway** | The Opta's own settings over its `$LGS` console: network, RS485 hub map, front-panel buttons, relay outputs and lamps, the clock and its scheduled reset — plus DFU firmware update and first-time QSPI provisioning |
| **Module Test** | **One module, everything.** The full R5.0 sweep (read → write → value limits → presets → display → light ring → optional unlock) with a live PASS/FAIL table and CSV export |
| **Danger** | Factory reset (type-the-ID + double confirm), save-to-EEPROM, software reset, clear statistics, set slave ID — with post-reboot probes |

Released firmware ships **inside** the tool (`app/blobs/`), so a site visit needs no
download: the module's factory and OTA images and the gateway's own. Each is verified
against the released file's SHA-256 before it is used.

A transaction log pane (all sources, raw TX/RX hex, CSV export) sits under every tab.

The header has a **language button** (English / ไทย), a theme picker and an About dialog
with the release notes. Language and theme are remembered in `data/config.json`. Protocol
identifiers — coil and register numbers, function codes, the transaction log — stay in
English in both languages so they always match `LGS-Control-Table.md`.

Safety is enforced in the worker, not just the UI: OTA coils 505-508 are always refused
(use `ota_sender.py`), danger coils only fire through the Danger tab, latch coils are
cooldown-gated (≥2.2 s), and the whole app funnels every transaction through one queue —
one Modbus client, one COM port / one TCP socket (the gateway accepts a single client).

## Hardware setups

1. **USB-RS485 dongle** → COM port, RTU 9600 8N1 (fixed framing, baud per module config).
2. **Arduino Opta as USB-RS485 bridge**: plug the Opta's USB-C, blue USER LED on = bridge
   active. The COM port is auto-detected and labeled. PC-side baud is ignored (USB CDC);
   the RS485 side always runs at 9600. The **Gateway tab is USB-only** — it talks the
   `$LGS` text console on this same port.
3. **Opta as Modbus TCP gateway** (`net.enabled=1` + LAN cable): **one client at a time** —
   a second connection is silently closed, which looks exactly like a dead gateway.

If the cabinet's RS485 runs through a **channel-switching hub**, the hub needs about two
seconds of silence to change channel. The gateway repairs that itself, but it shapes what
the tool can do: slots on one channel answer in ~100 ms each, and every extra channel in a
batch adds ~2 s to each polling sweep. The tool reads the row→channel map from the gateway
on every Gateway-tab read and groups its work accordingly.

Module addressing: grid slave ID = `row*10 + col` (rows 1-10, cols 1-8 → 11-18, 21-28,
… 101-108), factory default **247**, **246** = the temporary ID of a module whose switch
is in SET_ID mode (selectable as a target — e.g. to assign its real ID — but never
assignable itself), 0 = broadcast (not used by this tool). The header has a grid picker
next to the Slave ID field — click a number instead of typing; scans probe 246 and 247
in addition to the grid.
Module coils are combinations rather than steps — 1001 ring, 1011 ring + number, 1021
ring + latch, 1031 all three — and the latch coils only pulse when the module's own sense
reads *locked*. A slot whose drawer is already open reports the write as successful and
never moves the latch, so the tool reads reg 41 first and says so rather than passing it.

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
gateway ซึ่งรับทีละ 1 client — ต่อตัวที่สองจะถูกตัดเงียบๆ ดูเหมือน gateway ตาย)

แท็บหลัก: **Control** (ปุ่ม preset 1-8 / latch / display + อ่านเขียน register อิสระ),
**Monitor** (สถานะเครื่อง อุณหภูมิ health กลอน UID กระแส ตัวนับปุ่มยืนยัน),
**Installation Check** (ตรวจทั้งตู้ทีละหลายช่อง + **ซ้อมขั้นตอนหยิบยา** จุดไฟเป็นชุด
กดปุ่มยืนยันแล้วไฟดับ เลือกได้ว่าต้องปิดลิ้นชักก่อนหรือไม่), **Firmware (OTA)**
(อัปเดตเฟิร์มแวร์ผ่านบัส + สำรวจเวอร์ชันทั้งตู้ คลิกกลุ่มเวอร์ชันเพื่อตั้งเป้าหมายได้เลย),
**New Module** (แฟลชบอร์ดเปล่าผ่าน ST-Link พร้อมตั้ง ID), **Gateway** (ตั้งค่า Opta
ทั้งหมดผ่านคอนโซล `$LGS`: เครือข่าย ผัง hub ปุ่มหน้าตู้ ไฟสถานะ นาฬิกาและตารางรีเซต
รวมถึงอัปเดตเฟิร์มแวร์ผ่าน DFU), **Module Test**, **Danger**

**เฟิร์มแวร์ที่ปล่อยแล้วฝังมาในเครื่องมือ** ทั้งของโมดูลและของ gateway ออกหน้างานได้โดย
ไม่ต้องโหลดไฟล์ และตรวจ SHA-256 กับไฟล์ที่ปล่อยจริงทุกครั้งก่อนใช้

**ข้อควรรู้เรื่อง hub:** ถ้าบัส RS485 ผ่านฮับสลับช่อง ฮับต้องเงียบราว 2 วินาทีจึงจะสลับช่องได้
ช่องที่อยู่ฮับเดียวกันอ่านเร็วมาก (~100 ms ต่อช่อง) แต่ทุกช่องฮับที่เพิ่มเข้ามาในหนึ่งชุด
จะเพิ่มเวลาอีกราว 2 วินาทีต่อรอบ เครื่องมือจึงอ่านผังสายจาก gateway มาจัดกลุ่มงานให้เอง

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
