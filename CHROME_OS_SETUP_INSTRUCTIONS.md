# Chrome OS Keyboard Tester - One-Click Setup Instructions

## Important Limitation

**Enabling Crostini (Linux) on Chrome OS requires manual user interaction** - this is a Chrome OS security restriction that cannot be bypassed or automated.

## Setup Process (2 Steps Total)

### Step 1: Enable Crostini (Manual - One Time Only)
1. Open Chrome OS Settings
2. Go to "Linux (Beta)" section  
3. Click "Turn on" to set up Crostini
4. Wait for installation to complete (5-10 minutes)
5. Open the Terminal app (Linux terminal)

### Step 2: Run Setup Script (Automated)
1. Copy `setup_chromeos_keyboard_tester.sh` to your Linux files
2. In Terminal, run: `bash setup_chromeos_keyboard_tester.sh`
3. The script automatically installs:
   - Python 3
   - pip (package manager)
   - pynput library
   - Desktop shortcut

## After Setup

**To run the keyboard tester:**
- Double-click "Keyboard Tester" on your Linux desktop
- OR run: `~/keyboard_tester.sh`

## What This Achieves

- **One-time manual setup** (enabling Crostini)
- **Fully automated** Python and dependency installation
- **Desktop shortcut** for easy access
- **Full special key capture** capability

## Why Can't It Be Fully Automated?

Chrome OS security requires user confirmation to enable Linux (Crostini). This prevents malicious scripts from enabling Linux without user knowledge. Once Crostini is enabled, everything else can be automated.

## Alternative: HTML Version

If you prefer zero setup, use `ChromeOS_Keyboard_Test.html` - just double-click it in Chrome. However, it cannot capture system-level special keys due to browser security.
