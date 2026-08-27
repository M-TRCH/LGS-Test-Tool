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
| **Installation Check** | **Many modules, few commands.** One click selects the whole cabinet (the type picked in the header), or pick cells on the 10×8 map or the last scan result, then send one command per module — light, or light + the slot's number, optionally upgraded to throw the latch. Every cell turns green or red. Also holds the **Pick walkthrough**: a batch of slots lights together, someone picks them in any order, and each light goes out as its button is pressed — optionally not until the drawer is closed again. CSV export |
| **Firmware (OTA)** | Streams a module image over the bus, and surveys the **whole cabinet's firmware versions** — every slot coloured by the version it reports, with each version group clickable to become the update targets |
| **New Module** | Flashes a blank module over ST-Link and gives it its Modbus ID in one step, single or continuous |
| **Gateway** | The Opta's own settings over its `$LGS` console: network, RS485 hub map, front-panel buttons, relay outputs, the watchdog, and the clock with up to four scheduled resets a day — plus DFU firmware update and first-time QSPI provisioning. Warns when the gateway's cabinet size disagrees with the header's cabinet, with a one-click fix. Settings **export/import as a JSON file** — take a backup before a firmware upgrade that wipes the store; import stages values for the normal Save review and skips keys the firmware lacks |
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

The **cabinet type** (LGS 80 / 64 / 56 / 40, SMT type 12, or **Custom**) is picked once,
in the header, and remembered. Every whole-cabinet action follows it — the
installation check's and the firmware survey's "Whole cabinet" buttons, the gateway
hub map's default row count, and the check against the gateway's own cabinet
settings. Custom describes a shape of your own — how many rows, and how many slots
on each row (rows differ; LGS 64's middle rows are half width) — edited in a small
dialog and kept across restarts. On gateway ≥ 1.9.0 a non-catalogue shape can be
written to the gateway too (`panel.shape`), so the cabinet's own front-panel
buttons sweep the real slots; older firmware only accepts 40/64/80.

Safety is enforced in the worker, not just the UI: OTA coils 505-508 are always refused
(use `ota_sender.py`), danger coils only fire through the Danger tab, latch coils are
cooldown-gated (≥2.2 s), and the whole app funnels every transaction through one queue —
one Modbus client, one COM port / one TCP socket (the gateway accepts a single client).

## Hardware setups

1. **USB-RS485 dongle** → COM port, RTU 9600 8N1 (fixed framing, baud per module config).
2. **Arduino Opta as USB-RS485 bridge**: plug the Opta's USB-C, blue USER LED on = bridge
   active. The COM port is auto-detected and labeled. PC-side baud is ignored (USB CDC);
   the RS485 side always runs at 9600. The Gateway tab talks the `$LGS` text console on
   this same port.
3. **Opta as Modbus TCP gateway** (`net.enabled=1` + LAN cable): two clients since gateway
   fw v1.11.0 (a third is refused). Since gateway fw **v1.12.0 the Gateway tab works over
   TCP too** — the console tunnels through the same connection as Modbus (unit 255 /
   FC 0x41), so a site's server can read the config, change it, pull the event log, run
   the site report *with* its events section, and **update the gateway's firmware over
   the network**: the image is staged on the Opta's QSPI, CRC-verified there, and only
   then applied by its bootloader — a power cut or dropped link mid-upload changes
   nothing. Preparing a factory-fresh Opta (QSPI partitioning) still needs USB/DFU.

If the cabinet's RS485 runs through a **channel-switching hub**, the hub needs about two
seconds of silence to change channel. The gateway repairs that itself, but it shapes what
the tool can do: slots on one channel answer in ~100 ms each, and every extra channel in a
batch adds ~2 s to each polling sweep. The tool reads the row→channel map from the gateway
on every Gateway-tab read and groups its work accordingly.

Upgrading gateway firmware whose settings struct changed (v1.8.0 and v1.9.0 are two)
makes the Opta reject its stored config and come up on factory defaults — **Ethernet
off, no hub map**. **Export the config from the Gateway tab before flashing**, flash,
import, Save. The tool's own `data/config.json` keeps the hub map and the address, so
those two survive regardless.

One `$LGS` console caveat that shaped the tool: the gateway keeps SET values staged
across console sessions, so the tool discards the gateway's staged state before every
write — a save commits exactly what its review dialog showed. Console lines over ~120
characters are dropped whole, so multi-key writes go out in chunks.

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
land in `data/exports/`; every launch writes `data/logs/app-<date>.log` — stdout, stderr and
any unhandled exception on any thread, newest 20 kept.

Left running unattended — soaking the cabinet overnight, or serving NTP to a gateway — the
app asks Windows not to sleep for as long as a job is running. Windows standby ended the
first overnight soak at 00:17 and left no trace of itself anywhere but the gateway's own
event log; `app/keep_awake.py` and `app/applog.py` are the answer to both halves of that.

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
- **NTP server** (Gateway tab): serving time to gateways needs an *inbound UDP*
  firewall rule for the chosen port (default 123) — the first-run prompt only
  covered the web page's TCP listener. If Windows Time (w32time) already holds
  port 123, either stop it (`net stop w32time`, and set its startup type to
  Manual) or serve on another port and set the gateway's `net.ntp_port` to
  match. Needs gateway firmware 1.11.0+.
- Rebuild after any code change; the exe is a frozen snapshot.

## Server install (autorun at boot)

For the hospital's server PC, where the tool must come up after every reboot
with nobody logged in:

1. Copy the exe **and `install-autorun.ps1`** (both in `dist\` after a build)
   to a **local** folder, e.g. `C:\LGS-Test-Tool\` — never OneDrive or a
   network share (Files-On-Demand can dehydrate the exe before boot; the
   installer refuses such paths).
2. In an **admin** PowerShell:

   ```powershell
   cd C:\LGS-Test-Tool
   .\install-autorun.ps1 -Port 8090            # pick a free port; 8080 default
   Start-ScheduledTask -TaskName 'LGS Test Tool'   # start now, no reboot needed
   ```

   Add `-Firewall` to open the port for other PCs on the LAN; `-Remove`
   uninstalls the task (and the firewall rule) again.

What the task does: runs the exe as SYSTEM at boot + 60 s, headless
(`--port <N> --no-browser`), restarts it up to 3 times on failure, never
kills it on a time limit. The UI is then at `http://localhost:<port>` (or
`http://<server-ip>:<port>` from the LAN).

Notes for IT:

- The tool refuses to run twice (named mutex) — double-clicking the exe while
  the task runs just opens the browser to the running copy.
- If the port is taken by another program the tool exits with code 2 and the
  task retries; pick the port with `-Port` (stored nowhere else — the task's
  command line is the truth).
- Network use: outbound TCP to the gateway (default `192.168.0.202:502`);
  inbound TCP `<port>` for the web UI; inbound UDP 123 only if the built-in
  NTP server is enabled in the tool.
- Set the machine's power plan to never sleep. The tool holds a keep-awake
  request while a soak or the NTP server runs, but that vanishes if the
  process dies — the power plan is the real control.
- Config, logs, and CSV exports live in `data\` next to the exe.

## Run (Docker — TCP only)

```bash
docker build -t lgs-test-tool .
docker run -d -p 8080:8080 -v lgs_data:/app/data --name lgs-test-tool lgs-test-tool
```

Add `-p 123:123/udp` when the container should also serve NTP to gateways.

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

**รุ่นตู้** (LGS 80 / 64 / 56 / 40, SMT type 12 หรือ **กำหนดเอง**) เลือกครั้งเดียวที่แถบบนสุดและจำไว้ให้ —
ปุ่ม "ทั้งตู้" ทุกหน้า จำนวนชั้นของผัง hub และการตรวจเทียบ `panel.cabinet`
ฝั่ง gateway อ้างอิงค่านี้ค่าเดียวกันหมด แบบกำหนดเองระบุทรงตู้ได้อิสระ:
กี่ชั้น และชั้นละกี่ช่องแยกกันทีละชั้น (ตู้จริงไม่ใช่สี่เหลี่ยมเสมอ — LGS 64
ชั้นกลางแคบกว่า) แก้ไขในหน้าต่างเล็กๆ และจำข้ามการเปิดโปรแกรม

แท็บหลัก: **Control** (ปุ่ม preset 1-8 / latch / display + อ่านเขียน register อิสระ),
**Monitor** (สถานะเครื่อง อุณหภูมิ health กลอน UID กระแส ตัวนับปุ่มยืนยัน),
**Installation Check** (ตรวจทั้งตู้ทีละหลายช่อง + **ซ้อมขั้นตอนหยิบยา** จุดไฟเป็นชุด
กดปุ่มยืนยันแล้วไฟดับ เลือกได้ว่าต้องปิดลิ้นชักก่อนหรือไม่), **Firmware (OTA)**
(อัปเดตเฟิร์มแวร์ผ่านบัส + สำรวจเวอร์ชันทั้งตู้ คลิกกลุ่มเวอร์ชันเพื่อตั้งเป้าหมายได้เลย),
**New Module** (แฟลชบอร์ดเปล่าผ่าน ST-Link พร้อมตั้ง ID), **Gateway** (ตั้งค่า Opta
ทั้งหมดผ่านคอนโซล `$LGS`: เครือข่าย ผัง hub ปุ่มหน้าตู้ เอาต์พุตรีเลย์ watchdog
นาฬิกาและตารางรีเซตได้ถึงวันละ 4 ช่วง รวมถึงอัปเดตเฟิร์มแวร์ผ่าน DFU),
**Module Test**, **Danger**

**เฟิร์มแวร์ที่ปล่อยแล้วฝังมาในเครื่องมือ** ทั้งของโมดูลและของ gateway ออกหน้างานได้โดย
ไม่ต้องโหลดไฟล์ และตรวจ SHA-256 กับไฟล์ที่ปล่อยจริงทุกครั้งก่อนใช้

**ข้อควรรู้เรื่อง hub:** ถ้าบัส RS485 ผ่านฮับสลับช่อง ฮับต้องเงียบราว 2 วินาทีจึงจะสลับช่องได้
ช่องที่อยู่ฮับเดียวกันอ่านเร็วมาก (~100 ms ต่อช่อง) แต่ทุกช่องฮับที่เพิ่มเข้ามาในหนึ่งชุด
จะเพิ่มเวลาอีกราว 2 วินาทีต่อรอบ เครื่องมือจึงอ่านผังสายจาก gateway มาจัดกลุ่มงานให้เอง

**ข้อควรรู้เรื่องอัปเดตเฟิร์มแวร์ gateway:** ถ้าโครงสร้างค่าตั้งเปลี่ยน (เช่น v1.8.0)
Opta จะไม่รับค่าที่เก็บไว้และกลับไปใช้ค่าโรงงาน — **Ethernet ปิด ไม่มีผัง hub**
ควรอ่านหน้า Gateway เก็บไว้ก่อนแฟลช แล้วตั้งค่ากลับหลังแฟลช (ผัง hub กับหมายเลข IP
เครื่องมือเก็บไว้ใน `data/config.json` อยู่แล้ว)

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
