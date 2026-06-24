import json
import subprocess


def get_mac_battery_health():
    try:
        # Query the IORegistry directly for AppleSmartBattery data
        cmd = ["ioreg", "-rw", "0", "-a", "-n", "AppleSmartBattery"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # -a outputs native XML/JSON plist format, which Python can load cleanly if parsed
        # However, a quick property match via shell is often even more foolproof:
        if not result.stdout.strip():
            return {"error": "No battery found (Are you on a Mac desktop?)."}

        # Let's pull the precise integer values directly from ioreg
        def extract_val(key):
            # ioreg outputs keys like "MaxCapacity" = 4200
            for line in result.stdout.split("\n"):
                if key in line:
                    return int(line.split("=")[-1].strip())
            return None

        max_cap = extract_val("MaxCapacity")
        design_cap = extract_val("DesignCapacity")
        current_cap = extract_val("CurrentCapacity")
        cycle_count = extract_val("CycleCount")
        is_charging = extract_val("IsCharging")

        if max_cap and design_cap:
            # Health is Max Capacity / Factory Design Capacity
            health_pct = round((max_cap / design_cap) * 100, 1)
            # Current charge state
            charge_pct = round((current_cap / max_cap) * 100, 1)

            return {
                "Status": "Success",
                "Battery Health": f"{health_pct}%",
                "Current Charge": f"{charge_pct}%",
                "Cycle Count": cycle_count,
                "Max Capacity (mAh)": max_cap,
                "Design Capacity (mAh)": design_cap,
            }
        else:
            return {"error": "Could not parse battery capacity keys."}

    except subprocess.CalledProcessError as e:
        return {"error": f"Failed running ioreg: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


if __name__ == "__main__":
    battery_data = get_mac_battery_health()
    print(json.dumps(battery_data, indent=4))