# 🔊 Audio Jack Test - Integration Guide

## Overview
The Audio Jack test detects 3.5mm headphone/microphone jacks and verifies audio controller functionality.

**Created Files:**
- ✅ `AudioJackTest.ps1` - Audio jack detection script

---

## What It Tests

✅ **Headphone Jack** - Detects headphone/speaker output devices
✅ **Microphone Jack** - Detects microphone input devices  
✅ **Combo Jack** - Detects combined headset jacks (TRRS)
✅ **Audio Controllers** - Detects audio hardware (Realtek, IDT, etc.)
✅ **Audio Services** - Verifies Windows Audio services are running
✅ **Audio Endpoints** - Counts input/output endpoints

---

## Integration Steps

### Step 1: Add Audio Jack Card to MYWINTEST42.py

**Location:** After the `mic_card` section (around line 3700)

Add this code after the microphone card ends:

```python
# ══════════════════════════════════════════════════════════════════
# AUDIO JACK CARD
# ══════════════════════════════════════════════════════════════════
audiojack_card = card(test_row_compact_top, "🎧  Audio Jack Test", track_key="audiojack")
audiojack_card.pack_forget()

# Header with refresh button
aj_header_row = ctk.CTkFrame(audiojack_card, fg_color="transparent")
aj_header_row.pack(fill="x", padx=14, pady=(10,6))
ctk.CTkLabel(aj_header_row, text="🎧  Audio Jack Test", 
             font=ctk.CTkFont(size=14, weight="bold"), 
             text_color="#58a6ff").pack(side="left")

# Refresh button
def _audiojack_refresh():
    """Run audio jack detection test."""
    try:
        ui_call(lambda: audiojack_status.configure(text="Scanning audio jack devices...", text_color="#9fb3c8"))
        ui_call(lambda: audiojack_detail.configure(text=""))
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AudioJackTest.ps1")
        
        if not os.path.exists(script_path):
            ui_call(lambda: audiojack_status.configure(text=f"❌ Audio jack test script not found at {script_path}", text_color="#ff7b72"))
            return
        
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        # Parse output
        lines = result.stdout.strip().split('\n')
        parsed = {}
        for line in lines:
            if ':' in line:
                key, _, value = line.partition(':')
                parsed[key.strip()] = value.strip()
        
        if parsed.get('TEST_RESULT') == 'PASS':
            if parsed.get('TEST_MESSAGE'):
                status_text = f"✅ {parsed['TEST_MESSAGE']}"
            else:
                status_text = "✅ Audio jack detected and functional"
            
            ui_call(lambda: audiojack_status.configure(text=status_text, text_color="#7ee787"))
            ui_call(lambda: audiojack_card.set_pass())
            
            # Build detail text
            detail_text = ""
            if 'HEADPHONE_JACK_DETECTED' in parsed:
                detail_text += f"Headphone Jack: {'✅ Yes' if parsed['HEADPHONE_JACK_DETECTED'] == '1' else '❌ No'}\n"
            if 'MICROPHONE_JACK_DETECTED' in parsed:
                detail_text += f"Microphone Jack: {'✅ Yes' if parsed['MICROPHONE_JACK_DETECTED'] == '1' else '❌ No'}\n"
            if 'COMBO_JACK_DETECTED' in parsed:
                detail_text += f"Combo Jack: {'✅ Yes' if parsed['COMBO_JACK_DETECTED'] == '1' else '❌ No'}\n"
            if 'AUDIO_OUTPUT_ENDPOINTS' in parsed:
                detail_text += f"Output Endpoints: {parsed['AUDIO_OUTPUT_ENDPOINTS']}\n"
            if 'AUDIO_INPUT_ENDPOINTS' in parsed:
                detail_text += f"Input Endpoints: {parsed['AUDIO_INPUT_ENDPOINTS']}\n"
            
            ui_call(lambda: audiojack_detail.configure(text=detail_text))
        else:
            ui_call(lambda: audiojack_status.configure(text="⚠️ No audio jack devices detected", text_color="#ffa657"))
            ui_call(lambda: audiojack_detail.configure(text="Check audio drivers and connections"))
            
    except subprocess.TimeoutExpired:
        ui_call(lambda: audiojack_status.configure(text="⏱️ Audio jack test timed out", text_color="#ffa657"))
    except Exception as e:
        ui_call(lambda: audiojack_status.configure(text=f"❌ Error: {str(e)}", text_color="#ff7b72"))

# Refresh button
ctk.CTkButton(
    aj_header_row, 
    text="⟳", 
    width=28, 
    height=28, 
    fg_color="#444444", 
    hover_color="#555555", 
    command=lambda: threading.Thread(target=_audiojack_refresh, daemon=True).start()
).pack(side="right")

# Status label
audiojack_status = ctk.CTkLabel(audiojack_card, text="Click refresh to test audio jack", 
                                 font=ctk.CTkFont(size=12), text_color="#9fb3c8")
audiojack_status.pack(anchor="w", padx=14, pady=(0,6))

# Detail text area
audiojack_detail = ctk.CTkTextbox(audiojack_card, height=120, wrap="word",
                                   font=ctk.CTkFont(size=11, family="monospace"))
audiojack_detail.pack(fill="x", padx=14, pady=(0,10))
audiojack_detail.configure(state="disabled")

# Auto-advance: Audio Jack -> Brightness
def _on_audiojack_marked():
    def _show():
        try: _highlight_and_show(brightness_card)
        except: pass
        try: threading.Thread(target=_start_brightness_test, daemon=True).start()
        except: pass
    ui_call(_show)

try:
    if hasattr(audiojack_card, 'set_pass') and hasattr(audiojack_card, 'pass_btn'):
        _aj_orig_pass = audiojack_card.set_pass
        _aj_orig_fail = audiojack_card.set_fail

        def _aj_pass():
            _aj_orig_pass()
            if _sequence_running[0]:
                ui_call(lambda: _highlight_and_show(brightness_card))
                return
            _on_audiojack_marked()

        def _aj_fail():
            _aj_orig_fail()
            if _sequence_running[0]:
                ui_call(lambda: _highlight_and_show(brightness_card))
                return
            _on_audiojack_marked()

        audiojack_card.set_pass = _aj_pass
        audiojack_card.set_fail = _aj_fail
        audiojack_card.pass_btn.configure(command=_aj_pass)
        audiojack_card.fail_btn.configure(command=_aj_fail)
except Exception:
    pass
```

---

### Step 2: Update Microphone Auto-Advance

**Location:** Find `_on_mic_marked()` function (around line 3760)

**Change from:**
```python
def _on_mic_marked():
    """After Microphone PASS/FAIL, show Brightness card."""
    # ... shows brightness_card
```

**Change to:**
```python
def _on_mic_marked():
    """After Microphone PASS/FAIL, show Audio Jack card and start test."""
    def _show_and_start_audiojack():
        try:
            _highlight_and_show(audiojack_card)
        except Exception:
            pass
        try:
            threading.Thread(target=_audiojack_refresh, daemon=True).start()
        except Exception:
            pass
    ui_call(_show_and_start_audiojack)
```

---

### Step 3: Update sequence_keys

**Location:** Line 6596 in MYWINTEST42.py

**Change from:**
```python
sequence_keys = [
    "ag", "sys", "comp", "net", "bat", "tp", "spk", "mic", "br",
    "smartcard", "usb", "nfc", "fingerprint", "ts", "px", "cam", "kb", "act", "drv", "gpu", "enr", "vs"
]
```

**Change to:**
```python
sequence_keys = [
    "ag", "sys", "comp", "net", "bat", "tp", "spk", "mic", "audiojack", "br",
    "smartcard", "usb", "nfc", "fingerprint", "ts", "px", "cam", "kb", "act", "drv", "gpu", "enr", "vs"
]
```

---

### Step 4: Add to Card Mapping

**Location:** Line 6601 in MYWINTEST42.py

**Add to the dictionary:**
```python
def _get_card_by_key(key):
    try:
        return {
            'ag': ag_card,
            'sys': sys_card,
            # ... existing cards ...
            'mic': mic_card,
            'audiojack': audiojack_card,  # ← ADD THIS
            'br': brightness_card,
            # ... rest of cards ...
        }.get(key)
```

---

### Step 5: Add to Sidebar

**Location:** Around line 6570 in MYWINTEST42.py

**Add after Microphone:**
```python
add_sidebar_item("mic",  "🎙️ Microphone",      mic_card)
add_sidebar_item("audiojack", "🎧 Audio Jack", audiojack_card)  # ← ADD THIS
add_sidebar_item("br",   "☀️ Brightness",      brightness_card)
```

---

### Step 6: Update Test Labels

**Location:** Lines 645 and 1012 in MYWINTEST42.py

**Add:**
```python
'mic': 'Microphone',
'audiojack': 'Audio Jack',  # ← ADD THIS
'br': 'Brightness',
```

---

## Updated Test Sequence

After integration, the sequence will be:

1.  🔈 Audio Changer
2.  🖥️ System Info
3.  🧩 Components
4.  📶 Network Adapters
5.  🔋 Battery
6.  🖱️ Touchpad
7.  🔊 Speaker
8.  🎙️ Microphone
9.  **🎧 Audio Jack** ← NEW
10. ☀️ Brightness
11. 💳 Smart Card
12. 🔌 USB Port Detection
13. 📡 NFC Reader
14. 👆 Fingerprint Reader
15. 👆 Touchscreen
16. 🟥 Pixel Test
17. 📷 Camera
18. ⌨️ Keyboard
19. ✅ Activation
20. 💾 Drivers
21. 🎮 GPU
22. 🔐 Enrollment Check
23. 🛡️ Virus Scan

**Total: 23 tests**

---

## Test It

Run the PowerShell script directly to test:
```powershell
powershell -ExecutionPolicy Bypass -File AudioJackTest.ps1
```

Expected output:
```
=== AUDIO JACK TEST ===
AUDIO_CONTROLLER: Realtek High Definition Audio
AUDIO_CONTROLLER_STATUS: OK
HEADPHONE_DEVICE: Speakers (Realtek Audio)
HEADPHONE_STATUS: OK
AUDIO_SERVICE_NAME: AudioSrv
AUDIO_SERVICE_STATUS: Running
AUDIO_OUTPUT_ENDPOINTS: 1
AUDIO_INPUT_ENDPOINTS: 1
HEADPHONE_JACK_DETECTED: 1
MICROPHONE_JACK_DETECTED: 1
TEST_RESULT: PASS
TEST_MESSAGE: Audio jack (headphone + mic) detected and functional
```

---

## Summary

✅ Audio Jack test created and ready
✅ Detects headphone, mic, and combo jacks
✅ Verifies audio services and endpoints
✅ Integration guide with step-by-step instructions
✅ Fits logically between Microphone and Brightness tests

The Audio Jack test is ready to integrate! 🎧
