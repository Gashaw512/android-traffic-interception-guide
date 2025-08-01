                      🔧 Tooling Note: [See](/scripts/README.md) for the automated certificate installer for Android devices.

# 📡 Comprehensive Guide: Intercepting Android App Traffic with Genymotion & Burp Suite

A step-by-step walkthrough to intercept and analyze Android app traffic using **Genymotion**, **Burp Suite**, and **VirtualBox**.  
Ideal for penetration testers, security researchers, and developers working in controlled environments.

---

> ⚠️ **Security Notice**  
> This guide is intended strictly for **authorized penetration testing**, **security research**, and **educational purposes only**.  
> Ensure you have explicit permission before intercepting traffic from any application, device, or network.  
> Unauthorized interception may be **illegal** and **unethical**. The author assumes **no responsibility** for misuse.

---

## 📋 Table of Contents

1. [System Requirements](#1-system-requirements)  
2. [Prerequisites & Assumptions](#2-prerequisites--assumptions)  
3. [Initial Setup](#3-initial-setup)  
4. [Network Configuration](#4-network-configuration)  
5. [Burp Suite Configuration](#5-burp-suite-configuration)  
6. [Certificate Installation](#6-certificate-installation)  
7. [Proxy Configuration](#7-proxy-configuration)  
8. [Testing & Verification](#8-testing--verification)  
9. [Troubleshooting](#9-troubleshooting)  
10. [Advanced Configuration](#10-advanced-configuration)  
11. [Reference Materials](#11-reference-materials)  
12. [License](#license)

---

## 1. System Requirements

### ✅ Essential Components:

- **Host OS:** Windows 10/11 (64-bit)  
- **VirtualBox:** Latest version → [Download](https://www.virtualbox.org/)  
- **Genymotion:** Android emulator → [Download](https://www.genymotion.com/)  
- **Burp Suite:** Community or Professional → [Download](https://portswigger.net/burp)  
- **Git for Windows:** Includes OpenSSL tools → [Download](https://git-scm.com/)

### 💻 Recommended Specs:

- **CPU:** Quad-core (Intel VT-x / AMD-V enabled)  
- **RAM:** 8GB+ (allocate 4GB to Genymotion)  
- **Storage:** 20GB free space  
- **Network:** Stable internet connection

---

## 2. Prerequisites & Assumptions

Before following this guide, make sure you:

- Understand basic **ADB** usage  
- Know how to work in a **command-line environment** (PowerShell, Git Bash, Terminal)  
- Understand **proxy setup** and **HTTPS interception**  
- Have **admin rights** on your system  
- Are working in a **controlled, authorized test environment**

---

## 3. Initial Setup

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


### 📱 C. Create Android Virtual Device

1. Launch **Genymotion**
2. Add a new virtual device with the following specs:
   - **OS:** Android 11 (API 30)
   - **Model:** Google Pixel 4
   - **Image:** With Google Play Services
  
---

## 4. Network Configuration

### 📦 VirtualBox Settings

1. Open **VirtualBox**
2. Select your Genymotion VM → `Settings → Network`
3. Configure adapters:

   - **Adapter 1:**
     - Attached to: `Bridged Adapter`
     - Name: Your physical network interface

   - **Adapter 2:**
     - Attached to: `NAT`



### 🔍 Verify Genymotion Internet Access

```bash
adb shell ping 8.8.8.8
```
✅ You should receive successful ping responses.

---

## 5. Burp Suite Configuration

### 🔧 Proxy Setup

1. Open **Burp Suite**
2. Go to `Proxy → Proxy Settings `
3. Add a new proxy listener:
   - **Binding:** All interfaces
   - **Port:** `8080`
4. Enable interception:
   - Navigate to: `Proxy → Intercept → ON`
  
---

## 6. Certificate Installation

### 📜 Export Burp Certificate

- Go to: `Proxy → Proxy Settings → Import/Export CA Certificate`
- Export the certificate as **DER format**:
- Choose a file (Select directory where to save ) to export the CA certificate and save it as 
  `cert.der`


### 🔁 Convert DER to PEM

Convert the exported DER certificate to `PEM` format and rename it according to its hash.  `First you have to move the directory where you save the CA certificate as shown section` [Export Burp Certificate](#5-certificate-installation) 

For **Windows (PowerShell or CMD)**:

```powershell
openssl x509 -inform der -in cert.der -out burp.pem
ren burp.pem 9a5ba575.0
```
For **Git Bash, Linux, or macOS**:
```bash

openssl x509 -inform der -in cert.der -out burp.pem
mv burp.pem 9a5ba575.0

```
### 📲 Push Certificate to Android Device (Emulator)
```bash
adb root  
adb remount  
adb push 9a5ba575.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/9a5ba575.0
adb reboot
```


#### Automated Solution (burpDrop)

` For a faster, automated approach`, use [burpDrop](/scripts/) - `our purpose-built tool that automates certificate conversion and installation:
`
##### Installation:
```bash
pip install burpdrop
```
##### Usage:
```bash
# Interactive install
burpdrop install

# Direct path install
burpdrop install -c "/path/to/burp.der"

# View logs
burpdrop logs

# Run diagnostics
burpdrop diagnose
```
> 📘 Full Documentation: See (scripts/README.md) for complete burpDrop documentation.
---

## 7. Proxy Configuration

### 🧭 Option 1: Use Host IP (Recommended)

Find your host machine's IP address and set it as the proxy for the emulator:

```bash
ipconfig | findstr "IPv4"
adb shell settings put global http_proxy <your_host_ip>:8080
```
Replace <your_host_ip> with the IP address of your host machine.

### 🔁 Option 2: Using Localhost (Alternative)
If you prefer to use localhost, set the proxy and reverse the ports:
```bash
adb shell settings put global http_proxy 127.0.0.1:3333
adb reverse tcp:3333 tcp:8080
```
### ❌ Disable Proxy
To disable the proxy on the emulator:
```bash

adb shell settings put global http_proxy :0

```
---
## 8. Testing & Verification

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
---
## 9. Troubleshooting

| Issue               | Solution                                              |
|---------------------|-------------------------------------------------------|
| **No traffic in Burp** | 1. Verify proxy IP<br>2. Check firewall<br>3. Ping host from ADB |
| **SSL errors**         | 1. Reinstall certificate<br>2. Check certificate permissions<br>3. Verify device system time |
| **adb remount fails**  | Run: `adb disable-verity` then `adb reboot`           |
| **Network unreachable**| Check VirtualBox → Bridged adapter settings            |
| **OpenSSL errors**     | Use Git Bash, not Windows CMD                          |
| **App bypasses proxy** | Use ProxyDroid or configure iptables manually          |

---
## 10. Advanced Configuration

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
---
---

## 11. Reference Materials

- [Genymotion Documentation](https://docs.genymotion.com/)
- [Burp Suite Documentation](https://portswigger.net/burp/documentation)
- [ADB Command Reference](https://developer.android.com/studio/command-line/adb)
- [VirtualBox Networking Guide](https://www.virtualbox.org/manual/ch06.html)

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

## ✉️ Contact

**Author:** Gashaw Kidanu  
**Email:** kidanugashaw@gmail.com     
**LinkedIn:** [linkedin.com/in/gashaw-kidanu](https://www.linkedin.com/in/gashaw-kidanu/)



