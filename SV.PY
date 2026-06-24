import sys
import traceback

# ✅ Catch crashes so the window doesn't close silently if it hits an issue
def excepthook(exc_type, exc_value, exc_tb):
    print("\n[CRITICAL ERROR DURING INITIALIZATION]")
    traceback.print_exception(exc_type, exc_value, exc_tb)
    input("\nPress ENTER to exit...")
sys.excepthook = excepthook


def check_hp_sureview_bios():
    """
    Queries the HP hardware firmware layer directly for HP Sure View privacy screens.
    Returns True if present, False if not capable, or None if not an HP unit.
    """
    if sys.platform != "win32":
        print("[-] Error: This script must be run on a Windows operating system.")
        return None
        
    try:
        import wmi
        
        print("[*] Connecting to root\\HP\\InstrumentedBIOS firmware layer...")
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
                print(f"[+] Found BIOS Feature (Backup Check): {name}")
                return True
                
        return False
        
    except ImportError:
        print("\n[!] Missing Dependency: The 'wmi' package is not installed.")
        print("    Fix: Open cmd and run: pip install wmi pywin32")
        return None
    except Exception as e:
        # If it's a non-HP machine, the namespace won't exist
        if "Invalid namespace" in str(e):
            return None
        else:
            print(f"[-] WMI query failed: {e}")
            return False


# --- Standalone Script Execution Loop ---
if __name__ == "__main__":
    print("============================================================")
    print("        DIAGNOSTIC: HP SURE VIEW BIOS HARDWARE CHECK        ")
    print("============================================================")
    
    try:
        result = check_hp_sureview_bios()
        
        print("\n" + "="*28 + " VERDICT " + "="*28)
        if result is True:
            print("RESULT: This unit is equipped with HP Sure View!")
        elif result is False:
            print("RESULT: HP Laptop detected, but it does not have a Sure View panel.")
        else:
            print("RESULT: Skipping BIOS Check (Not a business-class HP motherboard or environment error).")
        print("="*65)
            
    except Exception as e:
        print("\n[CRITICAL RUNTIME CRASH]")
        traceback.print_exc()
        
    # This guarantees the terminal stays completely open until you choose to exit
    input("\nPress ENTER to exit...")