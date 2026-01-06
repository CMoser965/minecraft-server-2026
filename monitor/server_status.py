import os
import requests
import time
import sys
import re
import threading
import queue
from datetime import datetime
from mcrcon import MCRcon

# --- Configuration ---
DUCKDNS_SUBDOMAIN = os.getenv("DUCKDNS_SUBDOMAIN")
STATUS_WEBHOOK_URL = os.getenv("DISCORD_SERVER_STATUS_WEBHOOK_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
SERVER_ADDRESS  = f"{DUCKDNS_SUBDOMAIN}.duckdns.org"

COORD_WEBHOOK_URL = os.getenv("COORDINATE_MAPPER_WEBHOOK_URL")
RCON_HOST = os.getenv("RCON_HOST", "mc")
RCON_PORT = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
LOG_FILE = "/data/logs/latest.log"

# Thread-safe queue for RCON jobs
job_queue = queue.Queue()

# --- Helper Functions ---
def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)

def send_coord_webhook(content):
    payload = {"username": "Cartographer", "content": content}
    try:
        requests.post(COORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        log(f"Failed to send Coord webhook: {e}")

def send_status_webhook(status, players=None, max_players=None, version=None):
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
        requests.post(STATUS_WEBHOOK_URL, json=payload)
    except Exception as e:
        log(f"Failed to send Status webhook: {e}")

# --- RCON Logic (Must run in Main Thread) ---
def process_coords_request(player, location_name):
    try:
        log(f"Processing RCON request for {player}...")
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            # Get Position
            pos_resp = mcr.command(f"data get entity {player} Pos")
            
            # Regex for: "[100.5d, 64.0d, -200.5d]"
            pos_match = re.search(r'\[(-?\d+\.?\d*)d?, (-?\d+\.?\d*)d?, (-?\d+\.?\d*)d?\]', pos_resp)
            
            # Get Dimension
            dim_resp = mcr.command(f"data get entity {player} Dimension")
            dim_match = re.search(r'minecraft:(\w+)', dim_resp)
            
            if pos_match:
                x, y, z = map(float, pos_match.groups())
                dimension = dim_match.group(1).capitalize() if dim_match else "Unknown"
                
                # Send Webhook
                msg = f"📍 **{location_name}**\n**Explorer:** `{player}`\n**Coordinates:** `{int(x)}, {int(y)}, {int(z)}` ({dimension})"
                send_coord_webhook(msg)
                
                # Confirm in-game
                mcr.command(f"tellraw {player} {{\"text\":\"Coordinates sent to Discord!\",\"color\":\"green\"}}")
                log(f"Success! Sent coords for {player}.")
            else:
                log(f"Could not parse position from: {pos_resp}")
            
    except Exception as e:
        log(f"RCON Error: {e}")

# --- Background Log Listener ---
def tail_logs():
    log(f"Log Listener started at: {LOG_FILE}")
    
    # Wait for file
    while not os.path.exists(LOG_FILE):
        time.sleep(5)
    
    with open(LOG_FILE, "r", encoding='utf-8', errors='ignore') as f:
        f.seek(0, 2) # Go to end
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            
            # Clean regex matching
            chat_match = re.search(r'<\s*(\w+)\s*>\s*!coords\s*(.*)', line)
            
            if chat_match:
                player = chat_match.group(1)
                location = chat_match.group(2).strip() or "Current Location"
                
                log(f"🎯 QUEUED: {player} -> {location}")
                
                # Push to queue for Main Thread to handle
                job_queue.put((player, location))

# --- Main Execution ---
def main():
    log(f"Starting services for {SERVER_ADDRESS}...")
    
    # 1. Start Log Listener (Background Thread)
    if COORD_WEBHOOK_URL and RCON_PASSWORD:
        t = threading.Thread(target=tail_logs)
        t.daemon = True
        t.start()
    else:
        log("Missing Config for Coords. Listener disabled.")

    # 2. Main Loop (Handles Status + Queue)
    last_status_check = 0
    last_state = "UNKNOWN"

    while True:
        current_time = time.time()

        # TASK A: Process Pending RCON Jobs (Every 1s)
        try:
            while not job_queue.empty():
                player, location = job_queue.get_nowait()
                process_coords_request(player, location)
        except Exception as e:
            log(f"Queue Error: {e}")

        # TASK B: Check Server Status (Every CHECK_INTERVAL seconds)
        if current_time - last_status_check > CHECK_INTERVAL:
            try:
                api_url = f"https://api.mcstatus.io/v2/status/java/{SERVER_ADDRESS}"
                response = requests.get(api_url, timeout=10)
                data = response.json()
                
                is_online = data.get("online", False)
                current_state = "ONLINE" if is_online else "OFFLINE"

                if current_state != last_state:
                    log(f"State change: {last_state} -> {current_state}")
                    
                    if is_online:
                        send_status_webhook("ONLINE", data["players"]["online"], data["players"]["max"], data["version"]["name_clean"])
                    else:
                        if last_state != "UNKNOWN":
                            send_status_webhook("OFFLINE")
                    
                    last_state = current_state
            
            except Exception as e:
                log(f"Error checking status: {e}")
            
            last_status_check = current_time

        # Sleep briefly to be kind to CPU
        time.sleep(1)

if __name__ == "__main__":
    main()