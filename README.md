# 📡 Comprehensive Guide: Intercepting Android App Traffic with Genymotion & Burp Suite

This repository provides a complete walkthrough for intercepting Android app traffic using **Genymotion**, **Burp Suite**, and **VirtualBox**. Designed for penetration testers, researchers, and developers seeking to analyze mobile app network activity.

---

## 📋 Table of Contents

1. [System Requirements](#1-system-requirements)  
2. [Initial Setup](#2-initial-setup)  
3. [Network Configuration](#3-network-configuration)  
4. [Burp Suite Configuration](#4-burp-suite-configuration)  
5. [Certificate Installation](#5-certificate-installation)  
6. [Proxy Configuration](#6-proxy-configuration)  
7. [Testing & Verification](#7-testing--verification)  
8. [Troubleshooting](#8-troubleshooting)  
9. [Advanced Configuration](#9-advanced-configuration)  
10. [Reference Materials](#10-reference-materials)  

---

## 1. System Requirements

### ✅ Essential Components:

- **Host OS:** Windows 10/11 (64-bit)  
- **VirtualBox:** Latest version → [Download](https://www.virtualbox.org/)  
- **Genymotion:** Android emulator → [Download](https://www.genymotion.com/)  
- **Burp Suite:** Community or Pro → [Download](https://portswigger.net/burp)  
- **Git for Windows:** Includes OpenSSL tools → [Download](https://git-scm.com/)

### 💻 Recommended Specs:

- **CPU:** Quad-core (Intel VT-x/AMD-V enabled)  
- **RAM:** 8GB+ (4GB allocated to Genymotion)  
- **Storage:** 20GB free space  
- **Network:** Stable internet connection

---

## 2. Initial Setup

### A. Disable Hyper-V (Windows Only)

```bash
bcdedit /set hypervisorlaunchtype off
```
✅ Restart your computer afterward.

### 🛠️ B. Install Tools in Order

- Install **VirtualBox**
- Install **Genymotion**
- Install **Git for Windows**
- Install **Burp Suite**

---

### 📱 C. Create Android Virtual Device

1. Launch **Genymotion**
2. Add a new virtual device with the following specs:
   - **OS:** Android 11 (API 30)
   - **Model:** Google Pixel 4
   - **Image:** With Google Play Services
## 3. Network Configuration

### 📦 VirtualBox Settings

1. Open **VirtualBox**
2. Select your Genymotion VM → `Settings → Network`
3. Configure adapters:

   - **Adapter 1:**
     - Attached to: `Bridged Adapter`
     - Name: Your physical network interface

   - **Adapter 2:**
     - Attached to: `NAT`

---

### 🔍 Verify Genymotion Internet Access

```bash
adb shell ping 8.8.8.8
```
✅ You should receive successful ping responses.

---

## 4. Burp Suite Configuration

### 🔧 Proxy Setup

1. Open **Burp Suite**
2. Go to `Proxy → Options`
3. Add a new proxy listener:
   - **Binding:** All interfaces
   - **Port:** `8080`
4. Enable interception:
   - Navigate to: `Proxy → Intercept → ON`
## 5. Certificate Installation

### 📜 Export Burp Certificate

- Go to: `Proxy → Options → Import/Export CA Certificate`
- Export the certificate as **DER format**:  
  `cert.der`

---

### 🔁 Convert DER to PEM

```bash
openssl x509 -inform der -in cert.der -out burp.pem
openssl x509 -inform pem -subject_hash_old -in burp.pem
ren burp.pem 9a5ba575.0
```
### 📲 Push Certificate to Android Device (Emulator)
```bash
adb root  
adb remount  
adb push 9a5ba575.0 /system/etc/security/cacerts
adb shell chmod 644 /system/etc/security/cacerts/9a5ba575.0
adb reboot
```
---
## 6. Proxy Configuration

### 🧭 Option 1: Use Host IP (Recommended)

```bash
ipconfig | findstr "IPv4"
adb shell settings put global http_proxy <your_host_ip>:8080
```
### 🔁 Option 2: Using Localhost (Alternative)
```bash
adb shell settings put global http_proxy 127.0.0.1:3333
adb reverse tcp:3333 tcp:8080
```
### ❌ Disable Proxy
```bash

adb shell settings put global http_proxy :0

```
---
## 7. Testing & Verification

### ✅ Basic Connection Tests

```bash
adb shell curl -v http://example.com
adb shell curl -v https://example.com

```
### 🔍 Verification Checklist

- ✅ Burp intercepts **HTTP** traffic  
- ✅ Burp intercepts **HTTPS** traffic  
- ✅ No SSL warnings in the device browser  
- ✅ Certificate appears under:  
  `Settings → Security → Trusted credentials`
### 🔗 ADB Connection Check

```bash
adb devices -l
```
Expected output:
```arduino
List of devices attached
192.168.XX.XXX:5555   device product:vbox86p model:Google_Pixel_4
```
## 8. Troubleshooting

| Issue               | Solution                                              |
|---------------------|-------------------------------------------------------|
| **No traffic in Burp** | 1. Verify proxy IP<br>2. Check firewall<br>3. Ping host from ADB |
| **SSL errors**         | 1. Reinstall certificate<br>2. Check certificate permissions<br>3. Verify device system time |
| **adb remount fails**  | Run: `adb disable-verity` then `adb reboot`           |
| **Network unreachable**| Check VirtualBox → Bridged adapter settings            |
| **OpenSSL errors**     | Use Git Bash, not Windows CMD                          |
| **App bypasses proxy** | Use ProxyDroid or configure iptables manually          |

---
## 9. Advanced Configuration

### 🧪 A. Bypass Certificate Pinning with Frida

```bash
pip install frida-tools
frida -U -f com.target.app -l ssl-pin-bypass.js
```
### 🔁 B. Persistent Proxy Setup
```bash
adb shell settings put global http_proxy <your_ip>:8080
adb shell "echo 'export HTTP_PROXY=http://<your_ip>:8080' >> /system/etc/profile"
```


