import sys

def check_hp_sureview_bios():
    """
    Queries the HP hardware firmware layer directly for Sure View privacy screens.
    Returns True if present, False if not capable, or None if not an HP unit.
    """
    if sys.platform != "win32":
        return None
        
    try:
        import wmi
        
        # Connect to the specialized HP business-class BIOS namespace
        hp_wmi = wmi.WMI(namespace=r"root\HP\InstrumentedBIOS")
        
        # Pull enumerations (toggles like Enabled/Disabled settings)
        bios_enums = hp_wmi.HP_BIOSEnumeration()
        
        for setting in bios_enums:
            name = getattr(setting, "Name", "")
            value = getattr(setting, "Value", "")
            
            # Check for the official 'Sure View' signature
            if "Sure View" in name or "SureView" in name:
                print(f"[+] Found BIOS Feature: {name}")
                print(f"[+] Current Active State: {value}")
                return True
                
        # Backup check in generic text attributes
        bios_settings = hp_wmi.HP_BIOSSetting()
        for setting in bios_settings:
            name = getattr(setting, "Name", "")
            if "Sure View" in name or "SureView" in name:
                return True
                
        return False
        
    except Exception:
        # Silently fail if namespace doesn't exist (e.g. running on a Getac, Dell, or Lenovo)
        return None

# --- Quick Test Execution ---
if __name__ == "__main__":
    result = check_hp_sureview_bios()
    if result is True:
        print("RESULT: This unit is equipped with HP Sure View!")
    elif result is False:
        print("RESULT: HP Laptop detected, but it does not have a Sure View panel.")
    else:
        print("RESULT: Skipping BIOS Check (Not a business-class HP motherboard).")