# 🔐 burpDrop – Burp CA Certificate Installer for Android Emulators

![Platform](https://img.shields.io/badge/Platform-Android%20Emulators-blue)
![Shell](https://img.shields.io/badge/Shell-.sh%20%26%20.bat-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Author](https://img.shields.io/badge/Author-Gashaw%20Kidanu-orange)

> Automate the conversion, backup, and installation of Burp Suite CA certificates into Android emulators with zero manual fuss.

---

## ✨ Features

- ✅ Linux/macOS (`burpDrop.sh`) and Windows (`burpDrop.bat`) support  
- 📦 Backup of existing certs before overwrite  
- 🧩 Automatic hash generation and PEM conversion  
- ⚙️ ADB root access and `/system` remount handled internally  
- 📜 Real-time logging and cleanup on exit

---

## 💡 Usage

### 🔧 Requirements
- Burp Suite (Export CA cert in **DER format**)  
- [Android Platform Tools](https://developer.android.com/studio/releases/platform-tools)  
- [OpenSSL](https://www.openssl.org/) in your system's `PATH`

---

### 🐧 Linux/macOS Instructions

```bash
chmod +x burpDrop.sh
./burpDrop.sh
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