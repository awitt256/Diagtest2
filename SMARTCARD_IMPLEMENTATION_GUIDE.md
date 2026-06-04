# Smart Card Reader Test Implementation Guide for MYWINTEST42.py

## Overview
This guide shows how to add a **Smart Card Reader** test card to your hardware test suite following the existing architecture patterns.

## Files Created
✅ `SmartCardTest.ps1` - PowerShell detection script (already created)

## Implementation Steps

### Step 1: Add Embedded PowerShell Script (Optional)
If you want to embed the PowerShell script directly in Python (like the enrollment script), add this near line 60 in MYWINTEST42.py:

```python
EMBEDDED_SMARTCARD_TEST_PS1 = r"""
# [Paste contents of SmartCardTest.ps1 here]
"""
```

### Step 2: Add Smart Card Test Card Creation
Insert this code after the port_card section (around line 4500):

```python
# ══════════════════════════════════════════════════════════════════
# SMART CARD READER CARD
# ══════════════════════════════════════════════════════════════════
smartcard_card = card(body, "💳  Smart Card Reader", track_key="smartcard")
try:
    smartcard_card.pack_forget()
except Exception:
    pass
try:
    smartcard_card.winfo_children()[0].destroy()
except Exception:
    pass

# Header with refresh button
sc_header_row = ctk.CTkFrame(smartcard_card, fg_color="transparent")
sc_header_row.pack(fill="x", padx=14, pady=(10,6))
ctk.CTkLabel(sc_header_row, text="💳  Smart Card Reader", 
             font=ctk.CTkFont(size=14, weight="bold"), 
             text_color="#58a6ff").pack(side="left")

# Refresh button
ctk.CTkButton(
    sc_header_row, 
    text="⟳", 
    width=28, 
    height=28, 
    fg_color="#444444", 
    hover_color="#555555", 
    command=lambda: threading.Thread(target=_smartcard_refresh, daemon=True).start()
).pack(side="right")

# Status display
sc_status = ctk.CTkLabel(
    smartcard_card,
    text="Checking for smart card readers...",
    font=ctk.CTkFont(size=12),
    text_color="#9fb3c8",
)
sc_status.pack(anchor="w", padx=14, pady=(0, 6))

# Smart card info display frame
sc_info_frame = ctk.CTkFrame(smartcard_card, fg_color="#0d1117", corner_radius=8)
sc_info_frame.pack(fill="x", padx=14, pady=(0, 10))

sc_service_lbl = ctk.CTkLabel(
    sc_info_frame, 
    text="Service: --", 
    font=ctk.CTkFont(size=11), 
    text_color="#9fb3c8"
)
sc_service_lbl.pack(anchor="w", padx=12, pady=(10, 4))

sc_readers_lbl = ctk.CTkLabel(
    sc_info_frame, 
    text="Readers Found: --", 
    font=ctk.CTkFont(size=11), 
    text_color="#9fb3c8"
)
sc_readers_lbl.pack(anchor="w", padx=12, pady=(4, 4))

sc_details_text = tk.Text(
    sc_info_frame,
    bg="#0d1117",
    fg="#c9d1d9",
    font=("Consolas", 10),
    height=6,
    wrap="word",
    borderwidth=0,
    highlightthickness=0,
)
sc_details_text.pack(fill="x", padx=12, pady=(4, 10))
sc_details_text.configure(state="disabled")

# Smart card detection variables
_sc_check_running = [False]

def _smartcard_refresh():
    """Run PowerShell script to detect smart card readers"""
    if _sc_check_running[0]:
        return
    _sc_check_running[0] = True
    
    try:
        ui_call(lambda: sc_status.configure(text="Detecting smart card readers...", text_color="#58a6ff"))
        
        # Run the PowerShell script
        ps_path = os.path.join(BASE, "SmartCardTest.ps1")
        
        if not os.path.exists(ps_path):
            ui_call(lambda: sc_status.configure(text="SmartCardTest.ps1 not found!", text_color="#ff7b72"))
            _sc_check_running[0] = False
            return
        
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        error = result.stderr
        
        # Parse the output
        service_name = "Not Found"
        service_status = "Unknown"
        readers_found = 0
        working_readers = 0
        reader_details = []
        test_result = "FAIL"
        
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith("SERVICE_NAME:"):
                service_name = line.split(":", 1)[1].strip()
            elif line.startswith("SERVICE_STATUS:"):
                service_status = line.split(":", 1)[1].strip()
            elif line.startswith("READER_FOUND:") and "NONE" not in line:
                readers_found += 1
                reader_details.append(line.split(":", 1)[1].strip())
            elif line.startswith("READER_STATUS:") and "OK" in line.upper():
                working_readers += 1
            elif line.startswith("TOTAL_READERS:"):
                readers_found = int(line.split(":", 1)[1].strip())
            elif line.startswith("WORKING_READERS:"):
                working_readers = int(line.split(":", 1)[1].strip())
            elif line.startswith("TEST_RESULT:"):
                test_result = line.split(":", 1)[1].strip()
        
        # Update UI
        def _update_ui():
            sc_status.configure(
                text=f"Smart Card Test: {test_result}",
                text_color="#7ee787" if test_result == "PASS" else "#ff7b72"
            )
            
            sc_service_lbl.configure(
                text=f"Service: {service_name} ({service_status})"
            )
            
            sc_readers_lbl.configure(
                text=f"Readers Found: {readers_found} ({working_readers} working)"
            )
            
            # Update details text
            sc_details_text.configure(state="normal")
            sc_details_text.delete(1.0, "end")
            
            if reader_details:
                sc_details_text.insert("end", "Detected Readers:\n")
                for i, reader in enumerate(reader_details, 1):
                    sc_details_text.insert("end", f"  {i}. {reader}\n")
            else:
                sc_details_text.insert("end", "No smart card readers detected.\n\n")
                sc_details_text.insert("end", "Possible reasons:\n")
                sc_details_text.insert("end", "  • No smart card reader hardware present\n")
                sc_details_text.insert("end", "  • Driver not installed\n")
                sc_details_text.insert("end", "  • Reader disabled in BIOS\n")
            
            sc_details_text.configure(state="disabled")
            
            # Auto-mark pass/fail
            if test_result == "PASS":
                if hasattr(smartcard_card, 'set_pass'):
                    smartcard_card.set_pass()
            else:
                if hasattr(smartcard_card, 'set_fail'):
                    smartcard_card.set_fail()
        
        ui_call(_update_ui)
        
    except subprocess.TimeoutExpired:
        ui_call(lambda: sc_status.configure(text="Smart card detection timed out", text_color="#ff7b72"))
    except Exception as e:
        ui_call(lambda: sc_status.configure(text=f"Error: {str(e)}", text_color="#ff7b72"))
    finally:
        _sc_check_running[0] = False

# AUTO ADVANCE: Add your next test here
def _on_smartcard_marked():
    """After Smart Card PASS/FAIL, show next card"""
    def _show_next():
        try:
            # Replace 'next_card' with your actual next test card
            _highlight_and_show(next_card)
        except Exception:
            pass
    ui_call(_show_next)

try:
    if hasattr(smartcard_card, 'set_pass') and hasattr(smartcard_card, 'set_fail'):
        _sc_orig_pass = smartcard_card.set_pass
        _sc_orig_fail = smartcard_card.set_fail
        
        def _sc_new_pass():
            _sc_orig_pass()
            _on_smartcard_marked()
            _log_sequence("smartcard result pass")
        
        def _sc_new_fail():
            _sc_orig_fail()
            _on_smartcard_marked()
            _log_sequence("smartcard result fail")
        
        smartcard_card.set_pass = _sc_new_pass
        smartcard_card.set_fail = _sc_new_fail
except Exception:
    pass
```

### Step 3: Add to Sequence Keys
Around line 6187, update the sequence_keys list:

```python
sequence_keys = [
    "ag", "sys", "comp", "net", "bat", "tp", "spk", "mic", "br",
    "port", "smartcard", "ts", "px", "cam", "kb", "act", "drv", "gpu", "enr", "vs"
]
```

### Step 4: Add to Card Mapping
Around line 6192, update the _get_card_by_key function:

```python
def _get_card_by_key(key):
    try:
        return {
            'ag': ag_card,
            'sys': sys_card,
            'comp': comp_card,
            'net': net_card,
            'bat': bat_card,
            'spk': spk_card,
            'mic': mic_card,
            'br': brightness_card,
            'tp': tp_card,
            'port': port_card,
            'smartcard': smartcard_card,  # <-- ADD THIS
            'ts': touchscreen_card,
            'px': pixel_card,
            'cam': cam_card,
            'kb': kb_card,
            'act': act_card,
            'drv': drv_card,
            'gpu': gpu_card,
            'enr': enroll_card,
            'vs': vs_card,
        }.get(key)
    except Exception:
        return None
```

### Step 5: Update Port Card Auto-Advance
Find the port card auto-advance section and modify it to point to smartcard_card instead of touchscreen_card:

```python
# Change from:
def _show_and_start_ts():
    _highlight_and_show(touchscreen_card)

# To:
def _show_and_start_smartcard():
    _highlight_and_show(smartcard_card)
    # Optionally auto-start smartcard test
    ui_call(lambda: threading.Thread(target=_smartcard_refresh, daemon=True).start())
```

## Testing the Implementation

1. **Test PowerShell Script First**:
   ```powershell
   .\SmartCardTest.ps1
   ```

2. **Run MYWINTEST42.py**:
   ```bash
   python MYWINTEST42.py
   ```

3. **Navigate to Smart Card Test**:
   - Either click "Run Sequence" to run full test suite
   - Or manually navigate to the Smart Card Reader card

## Expected Behavior

### If Smart Card Reader Present:
- ✅ Service status shows "Running"
- ✅ Reader name displayed
- ✅ Card auto-marks as PASS
- ✅ Green status indicator

### If No Smart Card Reader:
- ❌ Shows "No smart card readers detected"
- ❌ Card auto-marks as FAIL
- ❌ Red status indicator
- ℹ️ Helpful troubleshooting tips displayed

## Next Steps

After confirming Smart Card Reader test works, you can add:
1. **NFC Test** - Similar pattern, different PowerShell detection
2. **Fingerprint Reader** - Use Windows Biometric Framework
3. **Bluetooth Scan** - Use Bluetooth device enumeration

Would you like me to create the implementation for any of these next?
