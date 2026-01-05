import os
import requests
import time
import sys
from datetime import datetime

DUCKDNS_SUBDOMAIN = os.getenv("DUCKDNS_SUBDOMAIN")
WEBHOOK_URL = os.getenv("DISCORD_SERVER_STATUS_WEBHOOK_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))

SERVER_ADDRESS  = f"{DUCKDNS_SUBDOMAIN}.duckdns.org"


if not SERVER_ADDRESS or not WEBHOOK_URL:
    print("Error: Missing MC_SERVER_ADDRESS or DISCORD_WEBHOOK_URL env vars")
    sys.exit(1)

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)

def send_discord(status, players=None, max_players=None, version=None):
    if status == "ONLINE":
        color = 3066993 # Green
        desc = f"**Status:** 🟢 ONLINE\n**Address:** `{SERVER_ADDRESS}`\n**Players:** {players}/{max_players}\n**Version:** {version}"
    else:
        color = 15158332 # Red
        desc = f"**Status:** 🔴 OFFLINE\n**Address:** `{SERVER_ADDRESS}`\nServer is unreachable."

    payload = {
        "username": "Server Monitor",
        "embeds": [{
            "title": "Minecraft Server Status Update",
            "description": desc,
            "color": color,
            "footer": {"text": "Checked via mcstatus.io"}
        }]
    }
    
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        log(f"Failed to send Discord webhook: {e}")

def main():
    log(f"Starting monitor for {SERVER_ADDRESS}...")
    
    # Initial state assumption (Unknown)
    last_state = "UNKNOWN" 

    while True:
        try:
            # query api
            api_url = f"https://api.mcstatus.io/v2/status/java/{SERVER_ADDRESS}"
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            is_online = data.get("online", False)
            current_state = "ONLINE" if is_online else "OFFLINE"

            # Only alert if state CHANGED (or first run)
            if current_state != last_state:
                log(f"State change detected: {last_state} -> {current_state}")
                
                if is_online:
                    send_discord(
                        "ONLINE", 
                        data["players"]["online"], 
                        data["players"]["max"], 
                        data["version"]["name_clean"]
                    )
                else:
                    # Don't alert offline on first boot (prevents spam if restarting container)
                    if last_state != "UNKNOWN":
                        send_discord("OFFLINE")
                
                last_state = current_state
            
        except Exception as e:
            log(f"Error checking status: {e}")

        # Wait for next check
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()