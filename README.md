# LGS-Test-Tool

Web-based test tool (NiceGUI) for firing Modbus TCP/RTU commands at LGS R5.0 modules.

**Work in progress** — full README lands with the final commit.

## Run (native, Windows)

```powershell
& "C:\Users\mteer\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m app.main
```

Then open http://localhost:8080
