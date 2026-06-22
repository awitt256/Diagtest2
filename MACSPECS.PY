import subprocess
import sys
import re

def get_mac_marketing_specs():
    """
    Queries native macOS hardware channels and returns a dictionary 
    containing the Model, Identifier, EMC, and Order Number.
    """
    # Initialize default structure
    hardware_data = {
        "Marketing Name": "Unknown Mac",
        "Model Identifier": "Unknown",
        "Model Number": "Unknown",
        "EMC Number": "Unknown",
        "Order Number": "Unknown",
        "Serial Number": "Unknown"
    }
    
    if sys.platform != "darwin":
        return hardware_data

    try:
        # 1. Pull Model Identifier (e.g., MacBookAir10,1 or MacBook5,1)
        hardware_data["Model Identifier"] = subprocess.check_output(
            ["sysctl", "-n", "hw.model"]
        ).decode("utf-8").strip()
        
        # 2. Pull System Serial Number
        serial_out = subprocess.check_output(["ioreg", "-c", "IOPlatformExpertDevice", "-d", "2"]).decode("utf-8")
        serial_match = re.search(r'"IOPlatformSerialNumber"\s*=\s*"([^"]+)"', serial_out)
        if serial_match:
            hardware_data["Serial Number"] = serial_match.group(1)

        # 3. Pull Regulatory Model Number (The physical "A-Number" on the bottom case)
        root_ioreg = subprocess.check_output(["ioreg", "-rn", "/", "-d", "1"]).decode("utf-8")
        model_match = re.search(r'"model"\s*=\s*<"([^"]+)">', root_ioreg)
        if model_match:
            hardware_data["Model Number"] = model_match.group(1).strip()
            
    except Exception as e:
        print(f"Error gathering base hardware IDs: {e}")

    # 4. Cross-Reference local hardware matrix database
    # (Populate this matrix with the common units cycling through your workstation)
    hardware_matrix = {
        "MacBook5,1": {
            "name": "MacBook (13-inch, Aluminum, Late 2008)",
            "emc": "2254",
            "order": "MB467LL/A (2.4 GHz) / MB466LL/A (2.0 GHz)"
        },
        "MacBookAir10,1": {
            "name": "MacBook Air (M1, 2020)",
            "emc": "3598",
            "order": "MGN63LL/A / MGNA3LL/A"
        },
        "Mac14,2": {
            "name": "MacBook Air (M2, 2022, 8-CPU)",
            "emc": "8162",
            "order": "MLXW3LL/A / MLY33LL/A"
        },
        "MacBookPro18,1": {
            "name": "MacBook Pro (16-inch, M1 Pro, 2021)",
            "emc": "3681",
            "order": "MK183LL/A / MK1E3LL/A"
        }
    }
    
    # Map matching strings if found in target database
    current_id = hardware_data["Model Identifier"]
    if current_id in hardware_matrix:
        hardware_data["Marketing Name"] = hardware_matrix[current_id]["name"]
        hardware_data["EMC Number"] = hardware_matrix[current_id]["emc"]
        hardware_data["Order Number"] = hardware_matrix[current_id]["order"]
        
    return hardware_data

# --- Quick Test Execution ---
if __name__ == "__main__":
    specs = get_mac_marketing_specs()
    
    print("\n" + "="*40)
    print("     MAC HARDWARE LOGBOOK PROPERTIES   ")
    print("="*40)
    for key, val in specs.items():
        print(f"{key.ljust(18)}: {val}")
    print("="*40)