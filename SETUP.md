# Minecraft IGN Scanner - Setup & Usage Guide

## 1. Installation

### Prerequisites
*   **Python 3.8+** installed.
*   **Internet Connection**.

### Setup
1.  Open a terminal in the project folder.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/Mac
    venv\Scripts\activate     # On Windows (CMD)
    venv\Scripts\Activate.ps1 # On Windows (PowerShell)
    ```
    **PowerShell users:** If you get a "running scripts is disabled" error, run this first:
    ```powershell
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    ```
    Then try the activate command again.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## 2. Authentication (Bearer Token)

To scan names accurately, the tool needs a **Minecraft Bearer Token** from your account. This token allows the scanner to check "locked" names and claim available ones.

**How to get your token:**
1.  Open your web browser and go to: [https://www.minecraft.net/en-us/msaprofile](https://www.minecraft.net/en-us/msaprofile)
2.  Log in with your Microsoft/Minecraft account.
3.  Press **F12** to open Developer Tools.
4.  Click the **Network** tab.
5.  Refresh the page (**F5**).
6.  In the "Filter" box, type: `minecraftservices`.
7.  Click on any request (e.g., `attributes` or `privileges`).
8.  On the right side, click **Headers** (or "Request Headers").
9.  Find the line that says **Authorization**.
10. It will look like: `Bearer eyJhbGciOi...` (a very long string).
11. **Copy the entire token** (everything after "Bearer ").

**Saving the Token:**
*   You can paste it directly into the terminal when asked.
*   **Pro Tip:** Save it to a file named `token.txt` in the main folder. The script will load it automatically every time!

*Note: Tokens expire after 24 hours. If the script says "Auth Failed," just repeat these steps.*

---

## 3. Usage

Run the scanner:
```bash
python ign_scan.py
```

### Main Menu
*   **1. Start Scanner**: Begin hunting for names.
*   **2. Sniper Mode**: Browse names you've already found and claim them.

### Scan Modes
When starting a scan, you will choose a generation mode:
1.  **Random**: Generates random character strings (e.g., `x9k2`, `ab_1`). Infinite.
2.  **Dictionary Words**: Scans a massive list of ~370,000 English words (includes obscure terms).
3.  **Common Words**: Scans only the top 10,000 most common English words (clean, readable names).

### Proxies (Optional)
To scan faster or run multiple instances, you can use proxies.
1.  Create a file named `proxies.txt` in the folder (or rename `proxies_template.txt`).
2.  Add one proxy per line. Supported formats:
    *   `ip:port`
    *   `user:pass@ip:port`
    *   `socks5://ip:port`
3.  The script will automatically detect and rotate them.

---

## 4. File Structure
*   `scans/`: All your findings are saved here, organized by character length.
    *   `scans/3_characters/3_characters_ign_random.txt`
*   `Locked_IGNs.txt`: A list of names that are permanently blocked/duplicate (auto-managed).
*   `blacklisted_words.txt`: A list of "Not Allowed" words (auto-managed).

**Happy Hunting!**
