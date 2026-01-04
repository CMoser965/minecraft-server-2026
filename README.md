# 🚀 Unlucky Golem's 2026 Minecraft Server - Client Setup Guide

Welcome to the server! Follow these instructions exactly to get set up.

### 📋 Prerequisites
Before you start, ensure you have the following installed:
1. **Minecraft Java Edition** (Official Launcher).
2. **Java 17** (or Java 21). [Download here](https://adoptium.net/temurin/releases/?version=17) if you don't have it.

---

### Step 1: Install Forge
We are running on **Minecraft 1.20.1**.

1. Download the **Forge Installer (1.20.1)** from [here](https://files.minecraftforge.net/net/minecraftforge/forge/index_1.20.1.html).
   * *Note: Download the "Installer" (Recommended version).*
2. Run the `.jar` file you downloaded.
3. Select **"Install client"** and click **OK**.
4. Wait for it to say "Successfully installed client profile".

---

### Step 2: Download the Modpack
We use a custom sync script so you don't have to manually download mods.

1. **Download this Repository:**
   * Scroll to the top of this GitHub page.
   * Click the green **Code** button -> **Download ZIP**.
2. **Extract:**
   * Unzip the folder to somewhere safe (like your `Documents` or `Games` folder).
   * *Do not keep it in your Downloads folder.*

---

### Step 3: Sync the Mods
1. Open the folder you just extracted.
2. Double-click **`update-mods-client.bat`**.
   * A window will pop up and download all the required mods directly to your Minecraft folder.
   * **Success:** It will close automatically or say "Success".
   * **Failure?** Make sure you have Java installed globally.

---

### Step 4: Configure the Launcher (CRITICAL)
You **must** allocate more RAM, or the game will crash/lag immediately.

1. Open the **Minecraft Launcher**.
2. Go to the **Installations** tab at the top.
3. Find the **"forge-1.20.1..."** profile (it should have been created in Step 1).
4. Hover over it and click the **Three Dots (...)** -> **Edit**.
5. **Name:** Change it to "Unlucky Golem's 2026 Minecraft Server" (Optional).
6. **More Options:** Click this text to expand the settings.
7. **JVM Arguments:**
   * Look for the text `-Xmx2G` (it's usually at the start).
   * Change it to: **`-Xmx8G`**
   * *(Do not go higher than 10GB, even if you have 64GB of RAM).*
8. Click **Save**.

---

### Step 5: Play!
1. Select your new **Unlucky Golem's 2026 Minecraft Server** profile.
2. Click **Play**.
3. **Multiplayer** -> **Add Server**:
   * **Name:** Unlucky Golem's 2026 Minecraft Server
   * **Address:** `YOUR_PUBLIC_IP_HERE` (Ask Christopher for the IP)
4. Join!

---

### 🔄 How to Update
When new mods are added (jetpacks, nuclear reactors, etc.):

1. Go to your folder from **Step 2**.
2. Run **`update-mods-client.bat`** again.
3. Launch the game.
   * *The script will automatically delete old mods and download the new ones.*

---

### 🛠️ Troubleshooting

**Game Crashing on Startup?**
* Did you do **Step 4**? The pack requires at least 6-8GB of RAM.
* Are you using the official Forge 1.20.1 version?

**"Connection Refused"?**
* The server might be restarting or offline.

**Lag Spikes?**
* **Mouse Lag:** Lower your mouse polling rate to **500Hz** in your mouse software (Logitech/Razer).
* **Video Settings:** Turn **VSync OFF** and set Max Framerate to **Unlimited** or **165+**.