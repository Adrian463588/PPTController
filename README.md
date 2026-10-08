# PPTController 📱🎯

> **Aplikasi Smartphone Presentation Remote & Laser Pointer untuk Microsoft PowerPoint, Google Slides, dan Canva berbasis WebSockets, Python, dan Android ADB.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Android](https://img.shields.io/badge/Android-SDK%2034-3DDC84.svg?logo=android&logoColor=white)](https://developer.android.com)
[![Security: DevSecOps](https://img.shields.io/badge/DevSecOps-No%20Secrets%20Leaked-brightgreen.svg)](https://github.com)

---

### 📥 Download Aplikasi Android (Terbaru)
Unduh langsung file APK ke HP Android Anda untuk menikmati kontrol slide menggunakan tombol volume fisik:
* 📲 **[Download PPTRemote.apk (Versi Terbaru v1.1.0)](https://github.com/Adrian463588/PPTController/releases/latest/download/PPTRemote.apk)** *(GitHub Releases)*
* 📦 **[Download Langsung dari Repositori (Raw File)](https://raw.githubusercontent.com/Adrian463588/PPTController/main/PPTRemote.apk)** *(Mirror)*

---

## 📖 Ringkasan Proyek (Project Overview)

Saat melakukan presentasi penting (seperti sidang skripsi, seminar, pitch deck bisnis, atau kuliah umum), pembicara sering kali terbatas karena harus menekan tombol spasi atau panah di keyboard laptop secara manual, atau menggunakan pointer fisik konvensional.

**PPTController** mengubah smartphone (Android / iOS) Anda menjadi alat kendali presentasi profesional (*wireless presenter remote*) berlatensi sangat rendah (< 15 ms). 

Aplikasi ini mendukung kontrol navigasi slide dan pointer laser untuk berbagai platform presentasi populer:
* **Microsoft PowerPoint** (Slideshow fullscreen, Presenter View, dan mode edit)
* **Canva Presentation** (di Google Chrome, Edge, Firefox)
* **Google Slides**
* **PDF Presenter / Adobe Acrobat Reader**

---

## ✨ Fitur-Fitur Utama

1. **Navigasi Slide Universal & Responsif:**
   * **Tombol Sentuh di HP:** Tombol **NEXT** besar yang ramah jempol dan tombol **PREV**.
   * **Dukungan Tombol Volume Fisik (Android):** Tekan tombol fisik **Volume Up** pada bodi HP untuk *Next Slide* dan **Volume Down** untuk *Prev Slide*. Anda bisa berpindah slide tanpa perlu melihat layar HP atau bahkan saat HP berada di dalam saku jas/celana.
2. **Native Laser Pointer PowerPoint (`Ctrl + L`):**
   * Menggunakan engine laser pointer resmi bawaan Microsoft PowerPoint yang diakselerasi oleh GPU.
   * **Mode Touchpad:** Sentuh dan geser jempol di kotak touchpad HP untuk mengarahkan laser pointer secara presisi tanpa lag.
   * **Mode Air-Mouse (Gyroscope):** Arahkan HP di udara seperti remote pointer fisik menggunakan sensor orientasi ponsel.
   * Otomatis kembali ke kursor panah standar (`Ctrl + A`) saat sentuhan dilepas.
3. **Pintasan Presenter Terpadu:**
   * **Mulai Slideshow (`F5`):** Memulai presentasi dari awal.
   * **Lanjut Slideshow (`Shift + F5`):** Melanjutkan slide show dari slide aktif.
   * **Layar Hitam / Blackout (`B`):** Menggelapkan layar untuk menarik fokus audiens ke pembicara (dilengkapi proteksi sentuhan tak disengaja).
   * **Layar Putih / Whiteout (`W`):** Memutihkan layar.
   * **Keluar Presentasi (`Esc`):** Mengakhiri slide show.
   * **Canva Magic Shortcuts:** Tombol confetti (🎉), drumroll (🥁), bubbles (🫧), dan quiet (🤫).
4. **Ergonomi & Produktivitas Pembicara:**
   * **Stopwatch / Presentation Timer:** Penghitung durasi waktu presentasi langsung di layar HP agar durasi bicara tetap terkontrol.
   * **Haptic Vibration Feedback:** Ponsel bergetar lembut saat tombol ditekan sebagai konfirmasi taktil.
   * **Screen Wake-Lock:** Menjaga layar ponsel tidak terkunci atau mati otomatis selama presentasi berlangsung.
5. **Dua Mode Akses Fleksibel:**
   * **Mode Web PWA (Zero-Install):** Cukup scan QR Code dari kamera HP mana pun (Android/iPhone) tanpa perlu menginstal aplikasi.
   * **Mode Native Android APK (`PPTRemote.apk`):** Mengizinkan integrasi tombol fisik volume bodi ponsel.

---

## 🛠️ Tech Stack & Tools yang Digunakan

| Komponen | Teknologi / Tools | Keterangan |
| :--- | :--- | :--- |
| **Backend Server** | Python 3.12, FastAPI, Uvicorn, WebSockets | Server lokal real-time berlatensi ultra-rendah (<15ms) |
| **Desktop GUI Host** | Tkinter, Pillow, QRCode | Panel kontrol desktop laptop dengan tampilan QR Code |
| **Input Engine** | Windows Win32 API (`ctypes`), `user32.dll`, `pynput` | Injeksi keystroke tingkat native ke desktop interaktif (`WinSta0\default`) |
| **Mobile Web Remote** | HTML5, CSS3 Modern Dark Mode, JavaScript ES6 | WebSockets, Touch Events, Vibration API, Wake Lock API |
| **Android Companion** | Java, Android SDK 34, Android WebView, Gradle 8.9 | Menangkap event hardware `KEYCODE_VOLUME_UP` & `KEYCODE_VOLUME_DOWN` |
| **DevSecOps & Testing**| Pytest, GitHub CLI (`gh`), ADB (Android Debug Bridge) | Audit keamanan tanpa leak kredensial, automated test suite |

---

## 🚀 Panduan Penggunaan Langkah demi Langkah (Step-by-Step)

### Prasyarat:
* Laptop/PC berbasis **Windows 10 / 11**.
* Telah terinstal **Python 3.10+**.
* Smartphone (Android atau iOS) yang terhubung ke laptop melalui:
  * **Opsi 1 (USB Debugging / Kabel USB):** Paling direkomendasikan untuk stabilitas maksimal di ruang sidang/seminar.
  * **Opsi 2 (Wi-Fi / Hotspot):** Smartphone dan laptop berada di jaringan Wi-Fi yang sama atau HP mengaktifkan Personal Hotspot ke laptop.

---

### Langkah 1: Persiapan di Laptop (Host)

1. Clone repositori ini:
   ```bash
   git clone https://github.com/Adrian463588/PPTController.git
   cd PPTController
   ```

2. Instal dependensi Python yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

3. Jalankan server pengontrol:
   * **Cara Cepat:** Klik dua kali file `start_controller.bat`
   * **Atau lewat terminal:**
     ```bash
     python app.py
     ```
   Panel host akan muncul di layar laptop dan menampilkan **QR Code** serta URL server (misal: `http://192.168.0.5:8765`).

---

### Langkah 2: Menghubungkan Smartphone

Pilih salah satu metode koneksi berikut:

#### Metode A: Menggunakan Kabel USB (ADB USB Debugging) — *Paling Stabil*
1. Hubungkan HP Android ke laptop menggunakan kabel USB dan pastikan **USB Debugging** aktif.
2. Jalankan perintah reverse port forwarding sekali saja di terminal laptop:
   ```bash
   adb reverse tcp:8765 tcp:8765
   ```
3. Buka browser di HP Anda dan ketikkan alamat:
   ```
   http://127.0.0.1:8765
   ```
   *Atau* buka aplikasi **PPT Remote** di HP Android Anda, masukkan alamat `127.0.0.1:8765`, lalu tekan **Hubungkan**.

#### Metode B: Menggunakan Wi-Fi / Hotspot (Scan QR Code) — *Tanpa Kabel*
1. Pastikan HP dan laptop terhubung ke jaringan Wi-Fi yang sama (atau laptop terhubung ke Hotspot HP Anda).
2. Arahkan kamera HP ke **QR Code** yang tampil di layar laptop.
3. Buka tautan yang muncul. Antarmuka remote controller akan langsung terbuka di browser HP Anda.

---

### Langkah 3: Mengontrol Presentasi

1. Buka file presentasi Anda di laptop (Microsoft PowerPoint atau Canva).
2. Di layar smartphone:
   * Tekan tombol **▶ Mulai (F5)** untuk memulai slideshow presentasi.
   * Tekan tombol **NEXT** (atau tombol fisik **Volume Up** di HP) untuk maju ke slide berikutnya.
   * Tekan tombol **PREV** (atau tombol fisik **Volume Down** di HP) untuk mundur ke slide sebelumnya.
   * Geser jempol Anda di kotak touchpad HP untuk mengaktifkan dan menggerakkan **Laser Pointer Merah PowerPoint**.
   * Gunakan tombol timer **▶** di HP untuk memantau durasi waktu berbicara Anda.

---

## 🧪 Menjalankan Pengujian Otomatis (Automated Testing)

Proyek ini telah dilengkapi test suite otomatis menggunakan `pytest`:
```bash
python -m pytest tests/test_controller.py -v
```

---

## 🔒 Standar Keamanan & DevSecOps

Proyek ini dikembangkan dengan prinsip **DevSecOps**:
* **Zero Credential Leaks:** Tidak ada API key, token otentikasi, atau kredensial rahasia yang disimpan dalam repositori.
* **Sanitasi File:** Menggunakan `.gitignore` komprehensif untuk mencegah berkas sampah (*build artifacts*, cache Python/Gradle, dan log sesi) terunggah ke repositori publik.
* **Isolated Focus Control:** Input controller berinteraksi secara aman pada desktop interaktif Windows tanpa mengganggu proses sistem lainnya.

---

## 👤 Author / Signature

Dibuat dengan dedikasi oleh:
**Adrian Syah Abidin**
* GitHub: [@Adrian463588](https://github.com/Adrian463588)

---

## 📄 Lisensi

Didistribusikan di bawah lisensi MIT. Silakan gunakan dan modifikasi secara bebas untuk kebutuhan presentasi, riset, atau perkuliahan Anda.
