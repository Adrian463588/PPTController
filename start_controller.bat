@echo off
title PowerPoint & Canva Controller Host
echo ========================================================
echo   Memulai PowerPoint & Canva Remote Controller Host
echo ========================================================
cd /d "%~dp0"

echo Memeriksa dependensi Python...
python -m pip install -q -r requirements.txt

echo Menjalankan aplikasi...
python app.py
pause
