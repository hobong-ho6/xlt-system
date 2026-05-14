# 💻 XLT System v3.0 Complete Terminal Installation Guide

**Step-by-step guide for complete beginners - Follow along to install successfully**

---

## 🤔 **What is Terminal?**

**Terminal** is a text-based interface to communicate with your computer. It looks like the black screens with green text in hacker movies!

- **Don't worry**: It looks complex but you only need to copy & paste
- **It's safe**: Following this guide won't harm your computer  
- **It's efficient**: Once you learn it, it's the fastest and most reliable installation method

---

## 📋 **Pre-installation Checklist**

### ✅ **Requirements**

1. **macOS**: This guide is for Mac only
2. **Internet connection**: Wi-Fi or ethernet required
3. **Admin access**: You need to know your Mac password
4. **Time**: About 15-20 minutes needed

### 📱 **Basic Skills Needed**

- **Copy**: `⌘ + C` (Command + C)
- **Paste**: `⌘ + V` (Command + V)  
- **Enter key**: Execute commands
- That's all you need to know! 😊

---

## 🚀 **Step 1: Open Terminal**

There are several ways to open Terminal. Choose the easiest one for you!

### **Method A: Spotlight Search** (Easiest)

1. **Press `⌘ + Space` simultaneously**
   ```
   A search bar appears at the top of screen
   ```

2. **Type "terminal"**
   ```
   Terminal.app appears in search results
   ```

3. **Press Enter**
   ```
   A black or white window opens
   ```

### **Method B: Launchpad**

1. **Click Launchpad** in Dock (rocket icon)
2. **Click "Other" folder**
3. **Click "Terminal" app**

### **Method C: Finder**

1. **Open Finder** (first icon in Dock)
2. **Click "Applications" in left sidebar**
3. **Double-click "Utilities" folder**
4. **Double-click "Terminal"**

### 🎉 **Terminal is open if you see:**

Something like this on screen:
```
username@MacBook ~ %
```
or
```
username:~ username$
```

**If the cursor is blinking**, you're ready to enter commands!

---

## ⚡ **Step 2: Enter Installation Command**

### 📝 **What to do**

Simply **copy** the command below and **paste** it into Terminal!

### 🔗 **Installation Command** (Copy this)

```bash
curl -O https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_smart_update.command && chmod +x install_smart_update.command && ./install_smart_update.command
```

### 📋 **How to Copy & Paste**

1. **Select the entire command above** (drag with mouse)
2. **Copy**: `⌘ + C`
3. **Click Terminal window** (to make it active)
4. **Paste**: `⌘ + V`
5. **Press Enter**

### 🎬 **Expected Screen Output**

After entering the command and pressing Enter:

```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  9840  100  9840    0     0  26093      0 --:--:-- --:--:-- --:--:-- 26031
```

**This means the file is downloading**. Please wait!

---

## 🎯 **Step 3: Installation Process**

### 📺 **Welcome Screen**

After a moment, you'll see this nice display:

```
╔══════════════════════════════════════════════╗
║        XLT System v3.0 Smart Installation   ║
║      Version comparison + Auto-update        ║
╚══════════════════════════════════════════════╝

🔍 Checking versions...
   📱 Local version: 0.0.0
   🌐 Latest version: 3.0.0

🆕 New XLT System installation
   Version: v3.0.0

Proceed with installation? (Y/n):
```

### 💡 **First Choice**

When you see **"Proceed with installation? (Y/n):"**:

- **Type `Y` and press Enter** (capital or lowercase doesn't matter)
- Or **just press Enter** (default is Yes)

**Never press `n`!** It will cancel the installation.

### 📥 **Download Process**

```
📥 XLT System downloading...
   📦 Downloading source code from GitHub...
   📂 Extracting archive...
   📁 Moving to installation location: /Users/username/XLT-System
✅ GitHub download complete

🚀 XLT System installation starting...
```

**This process is automatic**. Don't type anything, just wait!

---

## 🔧 **Step 4: Dependencies Installation (User Choices Required)**

Now we install programs needed for XLT System. You'll need to make a few choices!

### 🐍 **Python Installation Choice**

```
[6/12] Python Environment Check and Installation
────────────────────────────────────────
❌ Python 3 is not installed.

🤖 Would you like to automatically install Python?

   1) Homebrew automatic installation (recommended - easy package management)
   2) Official installer download (fast - direct installation)
   3) Manual installation (visit python.org for manual setup)

Choose (1-3):
```

**👆 When you see this**: **Type `1` and press Enter**

- Option `1` is most stable and convenient
- Takes a bit longer but most reliable

### 📱 **Git Installation Choice**

```
[5/12] Git Version Control Tool Installation
────────────────────────────────────────
Git is useful for system updates and development. Install Git?
Install Git (Y/n):
```

**👆 When you see this**: **Type `Y` and press Enter**

- Git is useful for future updates
- Recommended to install

### 🎨 **Tray App Installation Choice**

```
[12/12] System Tray App Setup (Optional)
────────────────────────────────────────
Would you like to manage XLT System from the system tray?
Tray app allows server start/stop from menu bar.

Install tray app? (y/N):
```

**👆 When you see this**: **Type `y` and press Enter**

- Allows easy XLT System management from menu bar
- Convenient, so recommended to install

---

## 🔐 **Step 5: Password Entry (Normal Process)**

During installation, you might see this screen:

```
📦 Installing Python... (administrator access required)
Password:
```

**👆 When you see this**:

1. **Type your Mac login password** (characters won't show on screen - this is normal!)
2. **Press Enter**

**Important Notes**:
- **No ●●● symbols appear when typing password** - this is normal behavior!
- **Just type your password normally and press Enter**
- **If wrong, you'll be asked to try again**

---

## ⏳ **Step 6: Installation Progress**

Now installation proceeds automatically. You'll see content like this scroll by:

```
[1/12] System Environment Check
────────────────────────────────────────
✅ macOS system check complete

[2/12] Advanced Network Connectivity Check
────────────────────────────────────────
✅ Basic internet connection normal
✅ Google Translate API accessible

[3/12] System Performance Check
────────────────────────────────────────
CPU cores: 8, Memory: 16GB
✅ System performance sufficient

[4/12] Development Tools Installation
────────────────────────────────────────
📦 Installing Xcode Command Line Tools...
✅ Xcode Command Line Tools installation complete

[5/12] Git Version Control Tool Installation
────────────────────────────────────────
✅ Git installation complete

[6/12] Python Environment Check and Installation
────────────────────────────────────────
🍺 Python installation via Homebrew complete
✅ Python 3.11.8 installed

[7/12] Package Manager Upgrade
────────────────────────────────────────
✅ pip upgrade complete

[8/12] XLT System Dependencies Advanced Installation
────────────────────────────────────────
📚 Installing essential packages... (about 2-3 minutes)
   - EasyOCR (OCR engine)
   - Google Translate (translation API)
   - Flask (web server)
   - OpenPyXL (Excel processing)
   - Pillow (image processing)
   - PysTray (system tray)
✅ All dependencies installation complete

[9/12] Basic Configuration Creation
────────────────────────────────────────
✅ Working directory creation complete

[10/12] XLT System Initialization Verification
────────────────────────────────────────
✅ XLT System initialization successful

[11/12] Desktop Shortcut Creation
────────────────────────────────────────
✅ 'XLT System.command' shortcut created

[12/12] System Tray App Setup (Optional)
────────────────────────────────────────
✅ Tray app shortcut created
```

**💡 Don't type anything during this process!** It's all automatic.

---

## 🎉 **Step 7: Installation Complete**

Finally, installation is finished! You'll see this screen:

```
══════════════════════════════════════════════
🎉 XLT System v3.0 Complete installation finished!
══════════════════════════════════════════════

🚀 How to use:
  1️⃣  Double-click 'XLT System.command' on desktop
  2️⃣  Web browser auto-connects to http://localhost:5004
  3️⃣  Enter Figma URL to start translation!

💡 Would you like to start XLT System now?
Start now (Y/n):
```

**👆 When you see this**: **Type `Y` and press Enter**

Good to test it right away!

### 🌐 **Automatic Launch**

If you choose `Y`:

1. **Web browser opens automatically**
2. **`http://localhost:5004` page appears**
3. **If you see XLT System screen, installation successful!** 🎉

---

## 🧪 **Step 8: First Test**

If installation succeeded, let's test it!

### 🎨 **Test Figma URL**

Paste this URL into the input field on the web page:

```
https://www.figma.com/design/GOCHAYBS7hIrmWRGNuJOKV/Web3?node-id=42997-1033&t=PV0e598gBCKFl9CQ-1
```

### 📋 **Test Process**

1. **Enter Figma URL**
2. **Click "Extract OCR Text" button**
3. **Select some texts** (click checkboxes)
4. **Click "Translate Selected Texts" button**
5. **Download Excel file**

**If Excel file downloads successfully, you're all set!** 🎊

---

## ⚠️ **Troubleshooting**

### 🚫 **Problem 1: "curl: command not found"**

**Screen shows**:
```
-bash: curl: command not found
```

**Solution**:
- This error rarely occurs (curl is included with Mac)
- Close terminal completely and reopen
- If still doesn't work, check for macOS updates

### 🚫 **Problem 2: "Permission denied"**

**Screen shows**:
```
-bash: ./install_smart_update.command: Permission denied
```

**Solution**:
Enter this command in terminal:
```bash
chmod +x install_smart_update.command
```
Then run again:
```bash
./install_smart_update.command
```

### 🚫 **Problem 3: Download fails**

**Screen shows**:
```
curl: (6) Could not resolve host
```

**Solution**:
1. **Check Wi-Fi connection**
2. **Try again after a moment**
3. **If using VPN, turn it off and try**

### 🚫 **Problem 4: Password doesn't work**

**Screen shows**:
```
Sorry, try again.
Password:
```

**Solution**:
1. **Enter your Mac login password correctly**
2. **Characters won't show on screen - this is normal, type slowly**
3. **Check Caps Lock** (case sensitive)

### 🚫 **Problem 5: "Address already in use" port conflict**

**Screen shows**:
```
Address already in use
Port 5004 is in use by another program
```

**Solution**:
1. **XLT System is already running**
2. **Stop existing server in terminal**:
   ```bash
   pkill -f stable_web_server.py
   ```
3. **Wait a moment then retry installation**
4. **Or check if system is already working by visiting `http://localhost:5004` in browser**

### 🚫 **Problem 6: Installation hangs**

**Symptom**: Same screen for a long time with no progress

**Solution**:
1. **Wait 5 more minutes** (in case of slow network)
2. **Press `Ctrl + C` to cancel and retry**
3. **Close terminal completely and restart**

---

## 🎯 **How to Use After Installation**

### 🚀 **Starting XLT System**

**Method 1**: Desktop shortcut
- Double-click **"XLT System.command"** on desktop

**Method 2**: From terminal
```bash
cd ~/XLT-System
python3 stable_web_server.py
```

### 🌐 **Accessing Web Interface**

- Go to **`http://localhost:5004`** in browser
- Or it opens automatically when using shortcut

### ⚡ **Stopping Server**

- In terminal: **`Ctrl + C`** (Control + C)
- Or close terminal window

---

## 📞 **Need More Help?**

### 🆘 **Getting Support**

- **GitHub Issues**: https://github.com/hobong-ho6/xlt-system/issues
- **Please include detailed information**:
  - Which step had the problem
  - Error messages shown on screen
  - Your macOS version

### 📋 **Checking System Information**

Include this information when asking for help:

```bash
# Check macOS version
sw_vers

# Check installation location
ls ~/Desktop/XLT*.command

# Check Python version
python3 --version
```

---

## 🎊 **Congratulations!**

If you followed this guide to the end, you've successfully installed **XLT System v3.0**!

### ✨ **What You Can Do Now**

- 🎨 **Auto-extract text** from Figma designs
- 🌐 **Translate into 5 languages** simultaneously (Korean, English, Japanese, Chinese, Thai)
- 📊 **Auto-generate Excel files** with translation results
- 🔧 **Auto-handle placeholders** (variables like {{0}}, {{1}})
- 👁️ **Preview translations** before downloading

### 🚀 **Next Steps**

1. **Try first translation with test Figma URL**
2. **Apply to real projects**
3. **Check translation results in Excel files**

**🌟 Enjoy your translation work!**

---

**💡 Tip**: Once you learn this terminal installation method, it's the fastest and most reliable way. You can use the same command for future updates too!