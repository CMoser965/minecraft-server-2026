import os
import requests
import time
import sys
import re
import threading
import queue
from datetime import datetime
from mcrcon import MCRcon
from mcstatus import JavaServer

# --- Configuration ---
DUCKDNS_SUBDOMAIN = os.getenv("DUCKDNS_SUBDOMAIN")
STATUS_WEBHOOK_URL = os.getenv("DISCORD_SERVER_STATUS_WEBHOOK_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
SERVER_ADDRESS_PUBLIC = f"{DUCKDNS_SUBDOMAIN}.duckdns.org"

# INTERNAL address (Docker container name) - Faster & Reliable
SERVER_ADDRESS_INTERNAL = "mc" 
SERVER_PORT = 25565

COORD_WEBHOOK_URL = os.getenv("COORDINATE_MAPPER_WEBHOOK_URL")
RCON_HOST = os.getenv("RCON_HOST", "mc")
RCON_PORT = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
LOG_FILE = "/data/logs/latest.log"

job_queue = queue.Queue()

# --- Helper Functions ---
def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)

def send_webhook(url, payload):
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        log(f"Failed to send webhook: {e}")

def send_status_webhook(status, players=None, max_players=None, version=None):
    if status == "ONLINE":
        color = 3066993 # Green
        desc = f"**Status:** 🟢 ONLINE\n**Address:** `{SERVER_ADDRESS_PUBLIC}`\n**Players:** {players}/{max_players}\n**Version:** {version}"
    else:
        color = 15158332 # Red
        desc = f"**Status:** 🔴 OFFLINE\n**Address:** `{SERVER_ADDRESS_PUBLIC}`\nServer is unreachable."

    payload = {
        "username": "Server Monitor",
        "embeds": [{
            "title": "Minecraft Server Status Update",
            "description": desc,
            "color": color,
            "footer": {"text": "Checked via Local Docker Network"}
        }]
    }
    send_webhook(STATUS_WEBHOOK_URL, payload)

# --- RCON Logic ---
def process_coords_request(player, location_name):
    try:
        # Sanitize player name (remove non-alphanumeric just in case)
        player_clean = re.sub(r'\W+', '', player)
        
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            # 1. Get Pos
            pos_resp = mcr.command(f"data get entity {player_clean} Pos")
            # Matches: [100.5d, 64.0d, -200.5d] OR [100.5, 64.0, -200.5]
            pos_match = re.search(r'\[(-?\d+\.?\d*)d?, (-?\d+\.?\d*)d?, (-?\d+\.?\d*)d?\]', pos_resp)
            
            # 2. Get Dim
            dim_resp = mcr.command(f"data get entity {player_clean} Dimension")
            dim_match = re.search(r'minecraft:(\w+)', dim_resp)
            
            if pos_match:
                x, y, z = map(float, pos_match.groups())
                dimension = dim_match.group(1).capitalize() if dim_match else "Unknown"
                
                # Send Webhook
                msg = f"📍 **{location_name}**\n**Explorer:** `{player_clean}`\n**Coordinates:** `{int(x)}, {int(y)}, {int(z)}` ({dimension})"
                send_webhook(COORD_WEBHOOK_URL, {"username": "Cartographer", "content": msg})
                
                # Feedback in game
                mcr.command(f"tellraw {player_clean} {{\"text\":\"Coordinates sent to Discord!\",\"color\":\"green\"}}")
                log(f"Sent coords for {player_clean}")
            else:
                log(f"Failed to parse coords for {player_clean}. Resp: {pos_resp}")
            
    except Exception as e:
        log(f"RCON Error: {e}")

# --- Background Log Listener ---
def tail_logs():
    log(f"Log Listener started at: {LOG_FILE}")
    while not os.path.exists(LOG_FILE):
        time.sleep(5)
    
    with open(LOG_FILE, "r", encoding='utf-8', errors='ignore') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            
            # IMPROVED REGEX:
            # Looks for: <Name> !coords
            # But ignores timestamps/thread names at the start
            # Matches: "[12:00] [INFO]: <Player> !coords Base"
            if "!coords" in line:
                # Capture name inside < > closest to the command
                match = re.search(r'<\s*(\w+)\s*>\s*!coords\s*(.*)', line)
                if match:
                    player = match.group(1)
                    location = match.group(2).strip() or "Current Location"
                    log(f"🎯 QUEUED: {player} -> {location}")
                    job_queue.put((player, location))

# --- Main Execution ---
def main():
    log("Starting Local Monitor...")
    
    # Start Coords Listener
    if COORD_WEBHOOK_URL and RCON_PASSWORD:
        t = threading.Thread(target=tail_logs)
        t.daemon = True
        t.start()

    # Status Loop
    last_state = "UNKNOWN"
    server = JavaServer(SERVER_ADDRESS_INTERNAL, SERVER_PORT)

    while True:
        current_time = time.time()

        # 1. Process Queue (Coords)
        try:
            while not job_queue.empty():
                player, loc = job_queue.get_nowait()
                process_coords_request(player, loc)
        except Exception:
            pass

        # 2. Check Status (Local Ping)
        # We use a simple modulo check to respect CHECK_INTERVAL without blocking the queue loop
        if int(current_time) % CHECK_INTERVAL == 0:
            try:
                # Ping local container (fast!)
                status = server.status()
                current_state = "ONLINE"
                
                if current_state != last_state:
                    log(f"State change: {last_state} -> ONLINE")
                    send_status_webhook("ONLINE", status.players.online, status.players.max, status.version.name)
                    last_state = "ONLINE"
                    
            except Exception as e:
                # If ping fails
                if last_state != "OFFLINE":
                    log(f"State change: {last_state} -> OFFLINE ({e})")
                    if last_state != "UNKNOWN":
                        send_status_webhook("OFFLINE")
                    last_state = "OFFLINE"
            
            # Sleep 1s to prevent spamming during this second
            time.sleep(1.5) 
        else:
            time.sleep(1)

if __name__ == "__main__":
    main()