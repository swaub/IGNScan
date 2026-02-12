import requests
import random
import string
import time
import sys
import os
import shutil
import json
import concurrent.futures

# --- ANSI Color Constants ---
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"

# --- Constants ---
WORDLIST_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
WORDLIST_FILE = "words_alpha.txt"
COMMON_WORDS_URL = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt"
COMMON_WORDS_FILE = "common_words.txt"
BLACKLIST_FILE = "blacklisted_words.txt"
LOCKED_FILE = "Locked_IGNs.txt"
PROXIES_FILE = "proxies.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.minecraft.net",
    "Referer": "https://www.minecraft.net/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"'
}

PROXY_LIST = []

# --- UI Helper Functions ---

def enable_ansi():
    """Enable ANSI escape codes on Windows."""
    if os.name == 'nt':
        os.system('')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def header(title):
    """Print a styled header box."""
    width = 40
    pad = width - 2 - len(title)
    left = pad // 2
    right = pad - left
    print(f"\n{CYAN}{BOLD}")
    print(f"  {'=' * width}")
    print(f"  |{' ' * left}{title}{' ' * right}|")
    print(f"  {'=' * width}{RESET}")

def sub_header(title):
    """Print a smaller section header."""
    print(f"\n  {CYAN}{BOLD}--- {title} ---{RESET}")

def menu_option(num, label, desc=""):
    """Print a formatted menu option."""
    if desc:
        print(f"  {WHITE}{BOLD}[{num}]{RESET}  {label}  {DIM}{desc}{RESET}")
    else:
        print(f"  {WHITE}{BOLD}[{num}]{RESET}  {label}")

def prompt(text="Choice"):
    """Styled input prompt."""
    return input(f"\n  {YELLOW}>{RESET} {text}: ").strip()

def success(text):
    print(f"  {GREEN}{BOLD}[OK]{RESET} {text}")

def error(text):
    print(f"  {RED}{BOLD}[!]{RESET} {text}")

def warn(text):
    print(f"  {YELLOW}[*]{RESET} {text}")

def info(text):
    print(f"  {DIM}[i]{RESET} {text}")

def separator():
    print(f"  {DIM}{'─' * 40}{RESET}")

def pause(text="Press Enter to continue..."):
    input(f"\n  {DIM}{text}{RESET}")

def format_duration(seconds):
    """Format seconds into human-readable duration (e.g. '2h 15m 30s')."""
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    parts = []
    if seconds >= 3600:
        h = seconds // 3600
        seconds %= 3600
        parts.append(f"{h}h")
    if seconds >= 60:
        m = seconds // 60
        seconds %= 60
        parts.append(f"{m}m")
    if seconds > 0:
        parts.append(f"{seconds}s")
    return " ".join(parts)

# --- Data Helper Functions ---

def load_proxies():
    proxies = []
    if os.path.exists(PROXIES_FILE):
        try:
            with open(PROXIES_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    p = line.strip()
                    if p:
                        if not p.startswith("http") and not p.startswith("socks"):
                            p = f"http://{p}"
                        proxies.append(p)
            if proxies:
                info(f"Loaded {len(proxies)} proxies.")
        except Exception:
            pass
    return proxies

def get_session():
    sess = requests.Session()
    sess.headers.update(HEADERS)
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        sess.proxies = {"http": proxy, "https": proxy}
    return sess

def load_blacklist():
    blacklisted = set()
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        blacklisted.add(name)
        except Exception:
            pass
    return blacklisted

def append_to_blacklist(name):
    try:
        with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
    except Exception:
        pass

def load_locked_list():
    locked = set()
    if os.path.exists(LOCKED_FILE):
        try:
            with open(LOCKED_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        locked.add(name)
        except Exception:
            pass
    return locked

def append_to_locked_list(name):
    try:
        with open(LOCKED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
    except Exception:
        pass

def remove_from_locked_list(name, current_set):
    if name.lower() in current_set:
        current_set.remove(name.lower())
        try:
            with open(LOCKED_FILE, "w", encoding="utf-8") as f:
                for n in current_set:
                    f.write(f"{n}\n")
        except Exception:
            pass

def load_existing_results(filename):
    found = set()
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split(" [")
                    if len(parts) >= 2:
                        name = parts[0].strip().lower()
                        found.add(name)
        except Exception:
            pass
    return found

def download_file(url, filename, description="file"):
    if not os.path.exists(filename):
        info(f"Downloading {description}...")
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(r.text)
            success(f"{description} downloaded.")
        except Exception as e:
            error(f"Download failed: {e}")
            return False
    return True

def load_words(length, source_file=WORDLIST_FILE):
    if source_file == WORDLIST_FILE:
        if not download_file(WORDLIST_URL, WORDLIST_FILE, "full dictionary"):
            return []
    elif source_file == COMMON_WORDS_FILE:
        if not download_file(COMMON_WORDS_URL, COMMON_WORDS_FILE, "common words list"):
            return []
    valid_words = []
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if len(word) == length:
                    valid_words.append(word)
    except Exception:
        pass
    return valid_words

def generate_random_name(length):
    chars = string.ascii_lowercase + string.digits + '_'
    return ''.join(random.choice(chars) for _ in range(length))

def parse_duration(d_str):
    if not d_str:
        return None
    try:
        unit = d_str[-1].lower()
        val = int(d_str[:-1])
        return val * {"s": 1, "m": 60, "h": 3600, "d": 86400}.get(unit, 0)
    except Exception:
        return None

# --- Selenium Token Grabber ---

def _poll_browser_for_token(driver):
    """Poll a Selenium driver's CDP logs for a Minecraft Bearer token."""
    deadline = time.time() + 300  # 5 minute timeout
    poll_count = 0
    while time.time() < deadline:
        time.sleep(2)
        remaining = max(0, int(deadline - time.time()))
        mins, secs = divmod(remaining, 60)
        dots = "." * ((poll_count % 3) + 1)
        sys.stdout.write(f"\r  [*] Waiting for sign-in{dots: <4} ({mins}:{secs:02d} remaining)   ")
        sys.stdout.flush()
        poll_count += 1

        try:
            logs = driver.get_log("performance")
        except Exception:
            continue

        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
                if msg["method"] == "Network.requestWillBeSent":
                    url = msg["params"]["request"]["url"]
                    headers = msg["params"]["request"]["headers"]
                    if "minecraftservices.com" in url and "Authorization" in headers:
                        token = headers["Authorization"]
                        if token.lower().startswith("bearer "):
                            token = token[7:]
                        sys.stdout.write("\r" + " " * 60 + "\r")
                        sys.stdout.flush()
                        return token
            except (KeyError, json.JSONDecodeError):
                continue

    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()
    return None


def grab_token_from_browser():
    """Open a browser to Minecraft profile page and intercept the Bearer token.
    Uses a saved browser profile so the user only needs to sign in once."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        error("Selenium is not installed.")
        info("Run: pip install selenium webdriver-manager")
        return None

    # Also try to import Edge support
    try:
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        edge_available = True
    except ImportError:
        edge_available = False

    # Saved browser profile for persistent login sessions
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_profile")
    first_time = not os.path.exists(profile_dir)

    print()
    info("Launching browser...")
    if first_time:
        info("Sign in to Minecraft in the browser window.")
        info("Your session will be saved for future auto-refreshes.")
    else:
        info("Using saved session. Token should be grabbed automatically.")
        info("If prompted, sign in again to refresh your session.")
    info("Press Ctrl+C to cancel.\n")

    driver = None

    # Try Chrome first
    try:
        options = ChromeOptions()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument(f"--user-data-dir={profile_dir}")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.minecraft.net/en-us/msaprofile")

        token = _poll_browser_for_token(driver)
        driver.quit()
        driver = None

        if token:
            success("Token captured from browser!")
            return token
        error("Timed out waiting for sign-in (5 minutes).")
        return None

    except KeyboardInterrupt:
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()
        warn("Browser sign-in cancelled.")
        return None
    except Exception as chrome_err:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            driver = None

        if not edge_available:
            error(f"Chrome failed: {chrome_err}")
            info("Make sure Google Chrome or Microsoft Edge is installed.")
            return None

        # Fall back to Edge
        warn("Chrome not available. Trying Microsoft Edge...")

        try:
            options = EdgeOptions()
            options.set_capability("ms:loggingPrefs", {"performance": "ALL"})
            options.add_argument(f"--user-data-dir={profile_dir}")

            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            driver.get("https://www.minecraft.net/en-us/msaprofile")

            token = _poll_browser_for_token(driver)
            driver.quit()
            driver = None

            if token:
                success("Token captured from browser!")
                return token
            error("Timed out waiting for sign-in (5 minutes).")
            return None

        except KeyboardInterrupt:
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            warn("Browser sign-in cancelled.")
            return None
        except Exception as edge_err:
            error(f"Edge also failed: {edge_err}")
            info("Make sure Google Chrome or Microsoft Edge is installed.")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

# --- API Interaction ---

def check_names_bulk(names):
    url = "https://api.mojang.com/profiles/minecraft"
    taken_names = set()
    failed_names = set()
    chunks = [names[i:i + 10] for i in range(0, len(names), 10)]
    req_headers = HEADERS.copy()
    req_headers["Content-Type"] = "application/json"

    for chunk in chunks:
        while True:
            s = get_session()
            try:
                response = s.post(url, json=chunk, headers=req_headers, timeout=10)
                if response.status_code == 200:
                    for profile in response.json():
                        taken_names.add(profile['name'])
                    break
                elif response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 5))
                    time.sleep(wait)
                    continue
                elif 500 <= response.status_code < 600:
                    time.sleep(5)
                    continue
                else:
                    failed_names.update(chunk)
                    break
            except requests.RequestException:
                time.sleep(5)
        time.sleep(random.uniform(1.5, 2.5))

    return taken_names, failed_names


def verify_name(name):
    url = f"https://api.mojang.com/users/profiles/minecraft/{name}"
    while True:
        s = get_session()
        try:
            response = s.get(url, timeout=10)
            if response.status_code == 200:
                return "taken"
            elif response.status_code in [404, 204]:
                return "available"
            elif response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 10))
                time.sleep(wait)
                continue
            elif 500 <= response.status_code < 600:
                time.sleep(10)
                continue
            else:
                return "unknown"
        except requests.RequestException:
            time.sleep(10)
    return "unknown"


def check_name_status(name, bearer_token):
    url = f"https://api.minecraftservices.com/minecraft/profile/name/{name}/available"
    req_headers = HEADERS.copy()
    req_headers["Authorization"] = f"Bearer {bearer_token}"
    while True:
        s = get_session()
        try:
            response = s.get(url, headers=req_headers, timeout=10)
            if response.status_code == 200:
                time.sleep(8)
                return response.json().get("status", "unknown")
            elif response.status_code == 401:
                return "AUTH_EXPIRED"
            elif response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 10))
                time.sleep(wait)
                continue
            elif 500 <= response.status_code < 600:
                time.sleep(10)
                continue
            else:
                return "unknown"
        except requests.RequestException:
            time.sleep(10)
    return "unknown"


def claim_name(name, token):
    url = f"https://api.minecraftservices.com/minecraft/profile/name/{name}"
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.put(url, headers=headers, timeout=15)
        if response.status_code == 200:
            print()
            success(f"Claimed: {GREEN}{BOLD}{name}{RESET}")
            info("Log out and log back into your launcher to see the change.")
            return True
        elif response.status_code == 401:
            error("Authorization failed (401). Token may be expired.")
        elif response.status_code == 403:
            error("Forbidden (403). Possible reasons:")
            info("  You do not own Minecraft on this account.")
            info("  You changed your name within the last 30 days.")
            info("  The name was claimed moments ago.")
        elif response.status_code == 429:
            error("Rate limited (429). Too many requests.")
        elif response.status_code == 400:
            error("Bad request (400). Name may be invalid.")
        else:
            error(f"Failed with status {response.status_code}")
            info(f"Response: {response.text}")
    except Exception as e:
        error(f"Connection error: {e}")
    return False

# --- UI Screens ---

def prompt_bearer_token():
    clear_screen()
    header("AUTHENTICATION")

    # Try saved token first
    if os.path.exists("token.txt"):
        try:
            with open("token.txt", "r") as f:
                token = f.read().strip()
            if token:
                info("Loaded token from token.txt")
                warn("Validating token...")
                status = check_name_status("Notch", token)
                if status in ["TAKEN", "DUPLICATE", "AVAILABLE", "NOT_ALLOWED"]:
                    success("Token accepted!")
                    return token
                else:
                    warn("Saved token expired or invalid.")
                    os.remove("token.txt")
        except Exception:
            pass

    # Show auth method menu
    print()
    menu_option(1, "Auto", "Open browser & grab token")
    menu_option(2, "Manual", "Paste a Bearer Token")
    separator()

    while True:
        method = prompt("Auth method (1/2)")

        if method == "1":
            token = grab_token_from_browser()
            if token:
                warn("Validating token...")
                status = check_name_status("Notch", token)
                if status in ["TAKEN", "DUPLICATE", "AVAILABLE", "NOT_ALLOWED"]:
                    success("Token accepted!")
                    try:
                        with open("token.txt", "w", encoding="utf-8") as f:
                            f.write(token)
                        info("Token saved to token.txt")
                    except Exception:
                        pass
                    return token
                else:
                    error(f"Token validation failed (status: {status}).")
            else:
                error("Could not grab token from browser.")
            retry = prompt("Try again? (y/n)")
            if retry.lower() != 'y':
                return None

        elif method == "2":
            while True:
                token = prompt("Paste Bearer Token")

                if token.lower().startswith("bearer "):
                    token = token[7:].strip()
                if token.startswith('"') or token.startswith("'"):
                    token = token[1:-1]

                if not token:
                    continue

                warn("Validating token...")
                status = check_name_status("Notch", token)

                if status in ["TAKEN", "DUPLICATE", "AVAILABLE", "NOT_ALLOWED"]:
                    success("Token accepted!")
                    try:
                        with open("token.txt", "w", encoding="utf-8") as f:
                            f.write(token)
                        info("Token saved to token.txt")
                    except Exception:
                        pass
                    return token
                else:
                    error(f"Invalid token (status: {status}). Please get a fresh one.")
                    retry = prompt("Try again? (y/n)")
                    if retry.lower() != 'y':
                        return None
        else:
            error("Invalid choice.")


def browse_and_claim(token):
    base_dir = "scans"
    if not os.path.exists(base_dir):
        error("No 'scans' folder found. Run a scan first!")
        pause()
        return

    while True:
        clear_screen()
        header("SNIPER MODE")
        sub_header("Select Category")

        folders = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
        if not folders:
            warn("No scan folders found.")
            pause()
            return

        print()
        for i, folder in enumerate(folders):
            # Count available names in this folder
            count = 0
            folder_path = os.path.join(base_dir, folder)
            for fname in os.listdir(folder_path):
                if fname.endswith(".txt"):
                    try:
                        with open(os.path.join(folder_path, fname), "r") as f:
                            for line in f:
                                if "[AVAILABLE]" in line:
                                    count += 1
                    except Exception:
                        pass
            count_str = f"{DIM}({count} available){RESET}" if count > 0 else f"{DIM}(empty){RESET}"
            menu_option(i + 1, folder, count_str)

        separator()
        choice = prompt("Select folder, or 'b' to go back")
        if choice.lower() == 'b':
            return

        try:
            folder_idx = int(choice) - 1
            if not (0 <= folder_idx < len(folders)):
                error("Invalid selection.")
                time.sleep(1)
                continue
        except ValueError:
            error("Invalid input.")
            time.sleep(1)
            continue

        selected_folder = folders[folder_idx]
        folder_path = os.path.join(base_dir, selected_folder)

        # Level 2: Files
        while True:
            clear_screen()
            header("SNIPER MODE")
            sub_header(selected_folder)

            files = sorted([f for f in os.listdir(folder_path) if f.endswith(".txt")])
            if not files:
                warn("No result files in this folder.")
                pause()
                break

            print()
            for i, fname in enumerate(files):
                # Count available in this file
                count = 0
                try:
                    with open(os.path.join(folder_path, fname), "r") as f:
                        for line in f:
                            if "[AVAILABLE]" in line:
                                count += 1
                except Exception:
                    pass
                count_str = f"{DIM}({count} available){RESET}" if count > 0 else f"{DIM}(empty){RESET}"
                menu_option(i + 1, fname, count_str)

            separator()
            file_choice = prompt("Select file, or 'b' to go back")
            if file_choice.lower() == 'b':
                break

            try:
                file_idx = int(file_choice) - 1
                if not (0 <= file_idx < len(files)):
                    error("Invalid selection.")
                    time.sleep(1)
                    continue
            except ValueError:
                error("Invalid input.")
                time.sleep(1)
                continue

            selected_file = files[file_idx]
            file_path = os.path.join(folder_path, selected_file)

            # Level 3: Names
            while True:
                clear_screen()
                header("SNIPER MODE")
                sub_header(f"Available Names")
                info(f"File: {selected_file}")
                print()

                available_names = []
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if "[AVAILABLE]" in line:
                                name = line.split(" [")[0].strip()
                                available_names.append(name)
                except Exception:
                    pass

                if not available_names:
                    warn("No available names found in this file.")
                    pause()
                    break

                for i, name in enumerate(available_names):
                    print(f"  {WHITE}{BOLD}[{i + 1}]{RESET}  {GREEN}{name}{RESET}")

                separator()
                name_choice = prompt("Select # to claim, or 'b' to go back")
                if name_choice.lower() == 'b':
                    break

                try:
                    name_idx = int(name_choice) - 1
                    if not (0 <= name_idx < len(available_names)):
                        error("Invalid selection.")
                        time.sleep(1)
                        continue
                except ValueError:
                    error("Invalid input.")
                    time.sleep(1)
                    continue

                target_name = available_names[name_idx]
                print()
                warn("Re-verifying availability...")
                current_status = verify_name(target_name)
                if current_status != "available":
                    error(f"'{target_name}' is no longer available (status: {current_status}).")
                    pause()
                    continue

                success(f"'{target_name}' is still available!")
                warn(f"You are about to change your IGN to: {BOLD}{target_name}{RESET}")
                confirm = prompt(f"Type {BOLD}YES{RESET} to confirm")

                if confirm == "YES":
                    if claim_name(target_name, token):
                        # Mark as claimed — exact line match
                        try:
                            with open(file_path, "r") as f:
                                lines = f.readlines()
                            with open(file_path, "w") as f:
                                for line in lines:
                                    line_name = line.split(" [")[0].strip()
                                    if line_name == target_name and "[AVAILABLE]" in line:
                                        f.write(line.replace("[AVAILABLE]", "[CLAIMED BY YOU]"))
                                    else:
                                        f.write(line)
                        except Exception:
                            pass
                    pause()
                else:
                    info("Cancelled.")
                    time.sleep(1)


def delete_results():
    base_dir = "scans"
    if not os.path.exists(base_dir):
        error("No 'scans' folder found.")
        pause()
        return

    while True:
        clear_screen()
        header("CLEAR RESULTS")

        folders = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
        if not folders:
            warn("No folders found.")
            pause()
            return

        print()
        for i, folder in enumerate(folders):
            menu_option(i + 1, folder)

        separator()
        print(f"  {DIM}Type a number, '{RED}ALL{DIM}' to wipe everything, or 'b' to go back.{RESET}")
        choice = prompt("Choice")

        if choice.lower() == 'b':
            return

        if choice.lower() == 'all':
            print()
            warn(f"{RED}This will permanently delete ALL scan results.{RESET}")
            confirm = prompt(f"Type {RED}{BOLD}DELETE ALL{RESET} to confirm")
            if confirm == "DELETE ALL":
                shutil.rmtree(base_dir)
                os.makedirs(base_dir)
                success("All results deleted.")
                time.sleep(1)
                return
            info("Cancelled.")
            time.sleep(1)
            continue

        try:
            folder_idx = int(choice) - 1
            if not (0 <= folder_idx < len(folders)):
                error("Invalid selection.")
                time.sleep(1)
                continue
        except ValueError:
            error("Invalid input.")
            time.sleep(1)
            continue

        selected_folder = folders[folder_idx]
        folder_path = os.path.join(base_dir, selected_folder)

        while True:
            clear_screen()
            header("CLEAR RESULTS")
            sub_header(selected_folder)

            files = sorted([f for f in os.listdir(folder_path) if f.endswith(".txt")])
            if not files:
                warn("Folder is empty.")
                pause()
                break

            print()
            for i, fname in enumerate(files):
                menu_option(i + 1, fname)

            separator()
            print(f"  {DIM}Type a number, '{RED}FOLDER{DIM}' to delete entire folder, or 'b' to go back.{RESET}")
            file_choice = prompt("Choice")

            if file_choice.lower() == 'b':
                break

            if file_choice.lower() == 'folder':
                confirm = prompt(f"Delete folder '{RED}{selected_folder}{RESET}'? (y/n)")
                if confirm.lower() == 'y':
                    shutil.rmtree(folder_path)
                    success("Folder deleted.")
                    time.sleep(1)
                    break
                info("Cancelled.")
                time.sleep(1)
                continue

            try:
                file_idx = int(file_choice) - 1
                if not (0 <= file_idx < len(files)):
                    error("Invalid selection.")
                    time.sleep(1)
                    continue
            except ValueError:
                error("Invalid input.")
                time.sleep(1)
                continue

            target_file = files[file_idx]
            file_path = os.path.join(folder_path, target_file)
            confirm = prompt(f"Delete '{RED}{target_file}{RESET}'? (y/n)")
            if confirm.lower() == 'y':
                os.remove(file_path)
                success("File deleted.")
                time.sleep(1)
            else:
                info("Cancelled.")
                time.sleep(1)


def filter_results():
    base_dir = "scans"
    if not os.path.exists(base_dir):
        error("No scans found.")
        pause()
        return

    clear_screen()
    header("FILTER RESULTS")
    warn("Loading dictionary for analysis...")

    vocab = set()
    if os.path.exists(WORDLIST_FILE):
        with open(WORDLIST_FILE, "r") as f:
            for line in f:
                vocab.add(line.strip().lower())
    else:
        error("Dictionary file missing. Cannot filter.")
        pause()
        return

    leet_map = str.maketrans("013457", "oieast")
    clean_words = []
    leet_words = []
    total_found = 0

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r") as f:
                        for line in f:
                            if "[AVAILABLE]" in line:
                                name = line.split(" [")[0].strip().lower()
                                total_found += 1
                                if name in vocab:
                                    clean_words.append(name)
                                    continue
                                de_leeted = name.translate(leet_map)
                                if de_leeted != name and de_leeted in vocab:
                                    leet_words.append(f"{name} ({de_leeted})")
                except Exception:
                    pass

    clear_screen()
    header("FILTER RESULTS")
    print()
    info(f"Analyzed {total_found} available names.")
    print(f"  {GREEN}{BOLD}{len(clean_words)}{RESET} clean dictionary words")
    print(f"  {YELLOW}{BOLD}{len(leet_words)}{RESET} leet-speak words")
    separator()

    if clean_words:
        sub_header("Clean Words")
        print()
        for i in range(0, len(clean_words), 25):
            chunk = clean_words[i:i + 25]
            print(f"  {GREEN}{', '.join(chunk)}{RESET}")
            if i + 25 < len(clean_words):
                pause("Press Enter for more...")
        print()

    if leet_words:
        sub_header("Leet-Speak Words")
        print()
        for i in range(0, len(leet_words), 25):
            chunk = leet_words[i:i + 25]
            print(f"  {YELLOW}{', '.join(chunk)}{RESET}")
            if i + 25 < len(leet_words):
                pause("Press Enter for more...")

    if not clean_words and not leet_words:
        warn("No dictionary or leet-speak words found among available names.")

    pause()


def run_scanner(bearer_token):
    clear_screen()
    header("SCANNER SETUP")

    # 1. Character length
    print()
    while True:
        try:
            char_limit = int(prompt("Character length (3-16)"))
            if 3 <= char_limit <= 16:
                break
            error("Must be between 3 and 16.")
        except ValueError:
            error("Enter a valid number.")

    # 2. Generation mode
    sub_header("Generation Mode")
    print()
    menu_option(1, "Random", "e.g. 'x9_k2', 'ab3f'")
    menu_option(2, "Dictionary", "~370k English words")
    menu_option(3, "Common Words", "Top ~10k words")

    mode = "random"
    word_list = []
    while True:
        mode_input = prompt("Choice (1/2/3)")
        if mode_input == "1":
            mode = "random"
            break
        elif mode_input == "2":
            mode = "dictionary"
            info("Loading full dictionary...")
            word_list = load_words(char_limit, WORDLIST_FILE)
            if not word_list:
                warn(f"No words of length {char_limit}. Defaulting to Random.")
                mode = "random"
            else:
                success(f"Loaded {len(word_list)} words of length {char_limit}.")
            break
        elif mode_input == "3":
            mode = "common_words"
            info("Loading common words...")
            word_list = load_words(char_limit, COMMON_WORDS_FILE)
            if not word_list:
                warn(f"No common words of length {char_limit}. Defaulting to Random.")
                mode = "random"
            else:
                success(f"Loaded {len(word_list)} common words of length {char_limit}.")
            break
        else:
            error("Invalid choice.")

    # 3. Count / duration
    sub_header("Scan Target")
    target_count = float('inf')
    t_seconds = None
    while True:
        target_input = prompt("Count or duration (e.g. 5000, 1h, Enter=infinite)")
        if not target_input:
            break
        t_seconds = parse_duration(target_input)
        if t_seconds:
            break
        try:
            count = int(target_input)
            if count > 0:
                target_count = count
                break
            error("Enter a positive number.")
        except ValueError:
            error("Invalid input. Use a number or duration like '1h', '30m'.")

    # Prepare output
    output_dir = f"scans/{char_limit}_characters"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = f"{output_dir}/{char_limit}_characters_ign_{mode}.txt"

    # Load data
    separator()
    blacklisted_names = load_blacklist()
    locked_names = load_locked_list()
    global PROXY_LIST
    PROXY_LIST = load_proxies()
    already_found = load_existing_results(filename)

    if locked_names:
        print()
        skip = prompt(f"Skip {len(locked_names)} known locked names? (y/n)")
        if skip.lower() == 'y':
            info("Skipping locked names.")
            blacklisted_names.update(locked_names)
        else:
            info("Re-checking locked names.")

    # Filter word list for resume
    if mode in ["dictionary", "common_words"]:
        original_len = len(word_list)
        word_list = [w for w in word_list if w.lower() not in already_found]
        if len(word_list) < original_len:
            info(f"Skipping {original_len - len(word_list)} already-processed names.")
        random.shuffle(word_list)
    else:
        blacklisted_names.update(already_found)

    # Config summary
    clear_screen()
    header("SCANNING")
    print()

    mode_display = mode.replace('_', ' ').title()
    if t_seconds:
        count_display = format_duration(t_seconds)
    elif mode != "random":
        count_display = f"{len(word_list)} words"
    elif target_count == float('inf'):
        count_display = "Infinite"
    else:
        count_display = str(target_count)

    print(f"  {DIM}Length:{RESET}    {BOLD}{char_limit} characters{RESET}")
    print(f"  {DIM}Mode:{RESET}      {BOLD}{mode_display}{RESET}")
    print(f"  {DIM}Target:{RESET}    {BOLD}{count_display}{RESET}")
    print(f"  {DIM}Output:{RESET}    {BOLD}{filename}{RESET}")
    separator()
    info("Press Ctrl+C to pause/stop.\n")

    # Stats
    total_available = len(already_found)
    total_unavailable = 0
    total_not_allowed = len([n for n in blacklisted_names if len(n) == char_limit])
    total_locked = len([n for n in locked_names if len(n) == char_limit])
    total_unverified = 0
    auth_valid = True
    batch_size = 10
    names_since_pause = 0
    start_time = time.time()
    total_words = len(word_list) if mode in ["dictionary", "common_words"] else 0
    found_names = []
    last_found = ""

    def update_display(final=False):
        scanned = total_available + total_unavailable + total_not_allowed + total_locked + total_unverified
        elapsed = time.time() - start_time
        elapsed_str = format_duration(elapsed)
        speed = (scanned / elapsed * 60) if elapsed > 0 else 0

        if t_seconds:
            remaining = max(0, int(t_seconds - elapsed))
            rem_str = format_duration(remaining)
        elif mode == "random":
            rem_str = "Inf"
        else:
            rem_str = str(len(word_list))

        # Progress bar and ETA for dictionary/common word modes
        if total_words > 0:
            done = total_words - len(word_list)
            pct = min(100, int(done / total_words * 100))
            bar_width = 15
            filled = int(bar_width * done / total_words)
            bar = f"{'#' * filled}{'-' * (bar_width - filled)}"
            if speed > 0 and len(word_list) > 0:
                eta_seconds = len(word_list) / (speed / 60)
                eta_str = f" ETA: {format_duration(eta_seconds)}"
            else:
                eta_str = ""
            progress_str = f" [{bar}] {pct}%{eta_str}"
        else:
            progress_str = ""

        terminal_width = shutil.get_terminal_size((120, 24)).columns

        found_str = f" | >> {last_found}" if last_found else ""

        line = (
            f"  Scanned: {scanned}"
            f" | Avail: {total_available}"
            f" | Taken: {total_unavailable}"
            f" | {elapsed_str} @ {speed:.0f}/min"
            f"{progress_str}"
            f"{found_str}"
        )
        # Truncate to terminal width to prevent wrapping
        if len(line) >= terminal_width:
            line = line[:terminal_width - 1]
        else:
            line = line.ljust(terminal_width - 1)
        sys.stdout.write(f"\r{line}")
        if final:
            sys.stdout.write("\n")
        sys.stdout.flush()

    try:
        processed_count = 0
        while processed_count < target_count:
            if t_seconds and (time.time() - start_time) >= t_seconds:
                break
            try:
                current_batch_size = batch_size
                if target_count != float('inf'):
                    remaining = int(target_count - processed_count)
                    if remaining < batch_size:
                        current_batch_size = remaining
                if current_batch_size <= 0:
                    break

                # Generate batch
                batch_names = set()
                attempts = 0
                max_attempts = current_batch_size * 100

                while len(batch_names) < current_batch_size:
                    if mode in ["dictionary", "common_words"]:
                        if not word_list:
                            break
                        name = word_list.pop()
                    else:
                        name = generate_random_name(char_limit)

                    if name.lower() in blacklisted_names:
                        attempts += 1
                        if attempts > max_attempts:
                            break
                        continue

                    batch_names.add(name)
                    attempts += 1
                    if attempts > max_attempts:
                        break

                if not batch_names:
                    print()
                    warn("No more unique names to generate.")
                    break

                batch_list = list(batch_names)
                processed_count += len(batch_list)

                # Stage 1: Bulk check
                taken_set, failed_set = check_names_bulk(batch_list)

                candidates = []
                for name in batch_list:
                    if name in failed_set:
                        candidates.append(name)
                        continue
                    is_taken = False
                    for taken in taken_set:
                        if taken.lower() == name.lower():
                            total_unavailable += 1
                            is_taken = True
                            break
                    if not is_taken:
                        candidates.append(name)
                    else:
                        update_display()

                # Stage 2: Individual verify (threaded)
                stage2_candidates = []

                def verify_wrapper(n):
                    return n, verify_name(n)

                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_name = {executor.submit(verify_wrapper, n): n for n in candidates}
                    for future in concurrent.futures.as_completed(future_to_name):
                        name, result = future.result()
                        if result == "available":
                            stage2_candidates.append(name)
                        elif result == "taken":
                            total_unavailable += 1
                        else:
                            total_unverified += 1
                        update_display()

                # Stage 3: Authenticated check
                if auth_valid:
                    for name in stage2_candidates:
                        status = check_name_status(name, bearer_token)
                        res_status = ""

                        if status == "AVAILABLE":
                            total_available += 1
                            res_status = "AVAILABLE"
                            found_names.append(name)
                            last_found = name
                            if name.lower() in locked_names:
                                remove_from_locked_list(name, locked_names)
                        elif status == "TAKEN":
                            total_unavailable += 1
                            if name.lower() in locked_names:
                                remove_from_locked_list(name, locked_names)
                        elif status == "NOT_ALLOWED":
                            total_not_allowed += 1
                            if name.lower() not in blacklisted_names:
                                blacklisted_names.add(name.lower())
                                append_to_blacklist(name)
                        elif status == "DUPLICATE":
                            total_locked += 1
                            if name.lower() not in locked_names:
                                locked_names.add(name.lower())
                                append_to_locked_list(name)
                        elif status == "AUTH_EXPIRED":
                            sys.stdout.write("\n")
                            warn("Bearer token expired.")
                            info("Opening browser to grab a fresh token...")
                            new_token = grab_token_from_browser()
                            if new_token:
                                bearer_token = new_token
                                try:
                                    with open("token.txt", "w", encoding="utf-8") as f:
                                        f.write(new_token)
                                except Exception:
                                    pass
                                success("Token refreshed! Continuing scan.")
                                # Re-check this name with the new token
                                status = check_name_status(name, bearer_token)
                                if status == "AVAILABLE":
                                    total_available += 1
                                    res_status = "AVAILABLE"
                                    found_names.append(name)
                                    print(f"\n  >> FOUND: {name}")
                                elif status == "TAKEN":
                                    total_unavailable += 1
                                elif status == "NOT_ALLOWED":
                                    total_not_allowed += 1
                                    if name.lower() not in blacklisted_names:
                                        blacklisted_names.add(name.lower())
                                        append_to_blacklist(name)
                                elif status == "DUPLICATE":
                                    total_locked += 1
                                    if name.lower() not in locked_names:
                                        locked_names.add(name.lower())
                                        append_to_locked_list(name)
                                else:
                                    total_unverified += 1
                            else:
                                error("Could not refresh token. Auth disabled for this scan.")
                                auth_valid = False
                                total_unverified += 1
                        else:
                            total_unverified += 1

                        if res_status:
                            try:
                                with open(filename, "a", encoding="utf-8") as f:
                                    f.write(f"{name} [{res_status}]\n")
                            except Exception as e:
                                print(f"\n  [!] Failed to save result: {e}")

                        update_display()
                        time.sleep(0.5)

                # Cooldown
                names_since_pause += len(batch_list)
                if names_since_pause >= 50:
                    scanned = total_available + total_unavailable + total_not_allowed + total_locked + total_unverified
                    sys.stdout.write(f"\r  Scanned: {scanned} ... cooling down 3s")
                    sys.stdout.flush()
                    time.sleep(3)
                    update_display()
                    names_since_pause = 0

            except KeyboardInterrupt:
                sys.stdout.write("\n")
                warn("Scan paused.")
                choice = prompt("Quit to Main Menu? (y/n)")
                if choice.lower() == 'y':
                    break
                info("Resuming...")
                update_display()
                continue

    except KeyboardInterrupt:
        print()
        warn("Scan stopped.")

    # Final summary
    update_display(final=True)
    total = total_available + total_unavailable + total_not_allowed + total_locked + total_unverified

    print()
    print(f"  {CYAN}{'=' * 38}{RESET}")
    print(f"  {CYAN}{BOLD}  SCAN COMPLETE{RESET}")
    print(f"  {CYAN}{'=' * 38}{RESET}")
    print(f"  {DIM}Total Processed:{RESET}  {BOLD}{total}{RESET}")
    print(f"  {GREEN}Available:{RESET}        {BOLD}{total_available}{RESET}")
    print(f"  {RED}Taken:{RESET}            {BOLD}{total_unavailable}{RESET}")
    print(f"  {YELLOW}Locked:{RESET}           {BOLD}{total_locked}{RESET}")
    print(f"  {DIM}Blocked:{RESET}          {total_not_allowed}")
    print(f"  {DIM}Unverified:{RESET}       {total_unverified}")
    print(f"  {DIM}Elapsed:{RESET}          {format_duration(time.time() - start_time)}")
    print(f"  {DIM}Results:{RESET}          {filename}")
    print(f"  {CYAN}{'=' * 38}{RESET}")

    if found_names:
        print()
        print(f"  {GREEN}{BOLD}Names Found This Session:{RESET}")
        for n in found_names:
            print(f"    {GREEN}{n}{RESET}")

    pause("Press Enter to return to Main Menu...")


def main():
    enable_ansi()
    clear_screen()
    header("IGN SCANNER")

    bearer_token = prompt_bearer_token()
    if not bearer_token:
        error("Authentication failed. Exiting.")
        return

    # Ensure scans folder exists
    os.makedirs("scans", exist_ok=True)

    while True:
        clear_screen()
        header("IGN SCANNER")
        print()
        menu_option(1, "Start Scanner", "Scan for available names")
        menu_option(2, "Sniper Mode", "Browse & claim found names")
        menu_option(3, "Clear Results", "Delete scan results")
        menu_option(4, "Filter Results", "Find dictionary & leet words")
        menu_option(5, "Refresh Token", "Re-authenticate")
        menu_option(6, "Exit")

        choice = prompt("Choice")

        if choice == "1":
            run_scanner(bearer_token)
        elif choice == "2":
            browse_and_claim(bearer_token)
        elif choice == "3":
            delete_results()
        elif choice == "4":
            filter_results()
        elif choice == "5":
            new_token = prompt_bearer_token()
            if new_token:
                bearer_token = new_token
                success("Token refreshed!")
                time.sleep(1)
            else:
                warn("Kept existing token.")
                time.sleep(1)
        elif choice == "6":
            clear_screen()
            header("IGN SCANNER")
            print()
            info("Goodbye!")
            print()
            return
        else:
            error("Invalid choice.")
            time.sleep(1)


if __name__ == "__main__":
    main()
