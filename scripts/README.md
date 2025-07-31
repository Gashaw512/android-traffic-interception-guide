# 🔐 burpDrop – Burp CA Certificate Installer for Android Emulators

![Platform](https://img.shields.io/badge/Platform-Android%20Emulators-blue)
![Shell](https://img.shields.io/badge/Shell-.sh%20%7C%20.bat-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Author](https://img.shields.io/badge/Author-Gashaw%20Kidanu-orange)

> Seamlessly install [Burp Suite](https://portswigger.net/burp) CA certificates into rooted Android emulators.  
> Supports **Linux/macOS** and **Windows**, with automated conversion, backup, and deployment via ADB.

---

## ✨ Features

- ✅ Dual OS support: `burpDrop.sh` (Linux/macOS) & `burpDrop.bat` (Windows)
- 🔒 Converts Burp CA cert (DER → PEM → .0) with correct subject hash
- 🔁 Pushes cert to `/system/etc/security/cacerts/` on emulator
- 📦 Automatically backs up any existing cert with same hash
- 🧰 Verifies ADB/openssl availability and emulator state
- 🗂️ Logs installation history with timestamped logs

---

## 📦 Requirements

- **Burp Suite** installed (Community or Pro)
- Burp CA certificate exported in **DER format** (`cert.der`)
- [Android Platform Tools](https://developer.android.com/studio/releases/platform-tools) (`adb`)
- [OpenSSL](https://www.openssl.org/) available in your `PATH`
- Rooted Android emulator (e.g., [Genymotion](https://www.genymotion.com/))

---

## 🚀 Quick Start

### 🐧 Linux/macOS

```bash
chmod +x burpDrop.sh
./burpDrop.sh cert.der

```

### 🪟 Windows Instructions
```bat
burpDrop.bat

```

### 📁 Project Structure

burpDrop/
├── burpDrop.sh           # Shell script for Unix-like OS
├── burpDrop.bat          # Batch script for Windows
├── logs/                 # Auto-generated install logs
└── README.md             # You're reading it!
### 🖼️ Screenshots
Add a few images or terminal screenshots here showing script execution and success output for clarity and documentation polish.

### ❓ FAQ
1. How do I export the certificate from Burp? Go to Proxy > Options > CA Certificate > Export and select DER format.

2. Why does ADB remount fail? Verify the emulator supports root access (adb root). Genymotion typically works out of the box. For AVDs, you may need:

```bash
adb disable-verity
adb reboot
```
