@echo off
python scripts\one_click.py
python -m uvicorn Orpheus-FastAPI.app:app
