"""Entry script for the packaged Windows executable (see build_exe.ps1).

PyInstaller cannot use `python -m app.main` as an entry point, and the onefile
bootstrap re-executes the binary, so freeze_support() must run first.
"""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from app.main import run
    run()
