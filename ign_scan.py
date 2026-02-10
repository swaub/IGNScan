import requests
import random
import string
import time
import sys
import os
import concurrent.futures

# URL for a standard English word list
WORDLIST_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
WORDLIST_FILE = "words_alpha.txt"

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

# URL for Common English Words (Top 10,000)
COMMON_WORDS_URL = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt"
COMMON_WORDS_FILE = "common_words.txt"
BLACKLIST_FILE = "blacklisted_words.txt"
LOCKED_FILE = "Locked_IGNs.txt"
PROXIES_FILE = "proxies.txt"

# Browser-like headers to avoid 403 blocks
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

# Global proxy list
PROXY_LIST = []

def load_proxies():
    """Loads proxies from file."""
    proxies = []
    if os.path.exists(PROXIES_FILE):
        try:
            with open(PROXIES_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    p = line.strip()
                    if p:
                        # Auto-add http schema if missing
                        if not p.startswith("http") and not p.startswith("socks"):
                            p = f"http://{p}"
                        proxies.append(p)
            if proxies:
                print(f"Loaded {len(proxies)} proxies.")
        except Exception as e:
            print(f"Failed to load proxies: {e}")
    return proxies

def get_session():
    """Returns a session, optionally using a random proxy."""
    sess = requests.Session()
    sess.headers.update(HEADERS)
    
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        sess.proxies = {
            "http": proxy,
            "https": proxy
        }
    return sess

def load_blacklist():
    """Loads blacklisted words from file."""
    blacklisted = set()
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        blacklisted.add(name)
            print(f"Loaded {len(blacklisted)} blacklisted words.")
        except Exception as e:
            print(f"Failed to load blacklist: {e}")
    return blacklisted

def append_to_blacklist(name):
    """Appends a name to the blacklist file."""
    try:
        with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
    except Exception:
        pass

def load_locked_list():
    """Loads locked names from file."""
    locked = set()
    if os.path.exists(LOCKED_FILE):
        try:
            with open(LOCKED_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        locked.add(name)
            print(f"Loaded {len(locked)} previously locked accounts.")
        except Exception as e:
            print(f"Failed to load locked list: {e}")
    return locked

def append_to_locked_list(name):
    """Appends a name to the locked file."""
    try:
        with open(LOCKED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
    except Exception:
        pass

def remove_from_locked_list(name, current_set):
    """Removes a name from the locked list file and updates the set."""
    if name.lower() in current_set:
        current_set.remove(name.lower())
        # Rewrite the file (inefficient for huge lists, but removals are rare)
        try:
            with open(LOCKED_FILE, "w", encoding="utf-8") as f:
                for n in current_set:
                    f.write(f"{n}\n")
            print(f"  [Info] '{name}' was removed from the Locked List (it is no longer locked).")
        except Exception as e:
            print(f"Failed to update locked file: {e}")

def load_existing_results(filename):
    """Loads names that have already been found/scanned from the output file."""
    found = set()
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    # Parse lines like "name [AVAILABLE]"
                    parts = line.split(" [")
                    if len(parts) >= 2:
                        name = parts[0].strip().lower()
                        found.add(name)
            print(f"Loaded {len(found)} already processed names from {filename}.")
        except Exception as e:
            print(f"Failed to load existing results: {e}")
    return found

def download_file(url, filename, description="file"):
    """Generic file downloader."""
    if not os.path.exists(filename):
        print(f"Downloading {description} (this may take a moment)...")
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"{description} downloaded successfully.")
        except Exception as e:
            print(f"Failed to download {description}: {e}")
            return False
    return True

def download_wordlist():
    """Downloads the full dictionary."""
    return download_file(WORDLIST_URL, WORDLIST_FILE, "full dictionary")

def download_common_wordlist():
    """Downloads the common words dictionary."""
    return download_file(COMMON_WORDS_URL, COMMON_WORDS_FILE, "common words list")

def load_words(length, source_file=WORDLIST_FILE):
    """Loads words of a specific length from a source file."""
    # Ensure file exists
    if source_file == WORDLIST_FILE:
        if not download_wordlist(): return []
    elif source_file == COMMON_WORDS_FILE:
        if not download_common_wordlist(): return []

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

def check_names_bulk(names):
    """Check names via bulk API. Retries indefinitely on rate limits/network errors."""
    url = "https://api.mojang.com/profiles/minecraft"
    taken_names = set()
    failed_names = set()
    # Mojang API allows up to 10 names per request
    chunks = [names[i:i + 10] for i in range(0, len(names), 10)]
    
    # Merge headers
    req_headers = HEADERS.copy()
    req_headers["Content-Type"] = "application/json"

    for chunk in chunks:
        while True:
            # Get a session (potentially with a new proxy)
            s = get_session()
            try:
                # Use session for connection reuse
                response = s.post(url, json=chunk, headers=req_headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    for profile in data:
                        taken_names.add(profile['name'])
                    break # Success
                elif response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 5))
                    print(f"  [Bulk] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue # Retry
                else:
                    # Non-200, non-429 (e.g. 500, 503). Retry a few times then fail? 
                    # Actually, for 100% accuracy, we should retry 5xx errors too, but maybe fail on 400.
                    if 500 <= response.status_code < 600:
                        print(f"  [Bulk] Server error {response.status_code}. Retrying in 5s...")
                        time.sleep(5)
                        continue
                    
                    # 400 or other client error -> likely invalid name format in chunk
                    # print(f"  [Bulk] Failed with status {response.status_code}. Falling back to individual checks.")
                    failed_names.update(chunk)
                    break

            except requests.RequestException as e:
                # Network error — retry indefinitely
                print(f"  [Bulk] Network error: {e}. Retrying in 5s...")
                time.sleep(5)
        
        # Jitter: Random sleep 1.5s - 2.5s to look human
        time.sleep(random.uniform(1.5, 2.5))

    return taken_names, failed_names


def verify_name(name):
    """Verify a single name using the unauthenticated GET endpoint. Retries indefinitely on transient errors."""
    url = f"https://api.mojang.com/users/profiles/minecraft/{name}"
    
    while True:
        # Get a session (potentially with a new proxy)
        s = get_session()
        try:
            response = s.get(url, timeout=10)

            if response.status_code == 200:
                return "taken"
            elif response.status_code == 404 or response.status_code == 204:
                return "available"
            elif response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 10))
                print(f"  [Verify] Rate limited for '{name}'. Waiting {wait}s...")
                time.sleep(wait)
                continue
            elif 500 <= response.status_code < 600:
                print(f"  [Verify] Server error {response.status_code}. Retrying...")
                time.sleep(10)
                continue
            else:
                return "unknown" # Should rare (e.g. 400 Bad Request)
        except requests.RequestException:
            print(f"  [Verify] Network error for '{name}'. Retrying...")
            time.sleep(10)

    return "unknown"


def check_name_status(name, bearer_token):
    """Check name status via authenticated Minecraft services API. Retries indefinitely on transient errors."""
    url = f"https://api.minecraftservices.com/minecraft/profile/name/{name}/available"
    
    # Merge headers
    req_headers = HEADERS.copy()
    req_headers["Authorization"] = f"Bearer {bearer_token}"
    
    while True:
        # Get a session (potentially with a new proxy)
        s = get_session()
        try:
            response = s.get(url, headers=req_headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Hard throttle to protect account from rate limits when finding many names
                time.sleep(8)
                return data.get("status", "unknown")
            elif response.status_code == 401:
                return "AUTH_EXPIRED"
            elif response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 10))
                print(f"  [AuthCheck] Rate limited for '{name}'. Waiting {wait}s...")
                time.sleep(wait)
                continue
            elif 500 <= response.status_code < 600:
                print(f"  [AuthCheck] Server error {response.status_code}. Retrying...")
                time.sleep(10)
                continue
            else:
                return "unknown"
        except requests.RequestException:
             print(f"  [AuthCheck] Network error for '{name}'. Retrying...")
             time.sleep(10)

    return "unknown"

def prompt_bearer_token():

    """Prompts the user for a Minecraft bearer token."""

    print("\n--- Authentication Required ---")

    print("Please enter your Minecraft Bearer Token.")

    print("(See SETUP.md for instructions on how to get this token.)")

    print("-------------------------------------")



    while True:

        if os.path.exists("token.txt"):

            with open("token.txt", "r") as f:

                token = f.read().strip()

            print(f"Loaded token from token.txt")

        else:

            token = input("Paste Bearer Token: ").strip()



        # Cleanup

        if token.lower().startswith("bearer "):

            token = token[7:].strip()

        if token.startswith('"') or token.startswith("'"):

            token = token[1:-1]



        if not token:

            if os.path.exists("token.txt"):

                os.remove("token.txt")

            continue



        # Validate token

        print("Validating token...")

        status = check_name_status("Notch", token)

        if status in ["TAKEN", "DUPLICATE", "AVAILABLE", "NOT_ALLOWED"]:

            print(f"Token accepted! (Status: {status})")

            

            # Save the token for future use

            try:

                with open("token.txt", "w", encoding="utf-8") as f:

                    f.write(token)

                print("Token saved to token.txt")

            except:

                pass

            

            return token

        else:

            print(f"Invalid token (Status: {status}). Please get a fresh one.")

            if os.path.exists("token.txt"):

                os.remove("token.txt")

            retry = input("Try again? (y/n): ").lower()

            if retry != 'y':

                return None

def claim_name(name, token):
    """Attempts to change the Minecraft username to the target name."""
    print(f"\n[SNIPER] Attempting to claim IGN: {name} ...")
    print("------------------------------------------------")
    
    # Official endpoint for name change
    url = f"https://api.minecraftservices.com/minecraft/profile/name/{name}"
    # Merge headers manually since session might have other stuff
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    
    try:
        # PUT request is required for name change
        response = requests.put(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print(f"\n[!!!] SUCCESS! You have successfully claimed the name: {name}")
            print("      Log out and log back into your launcher to see changes.")
            return True
        elif response.status_code == 401:
            print(f"\n[FAILED] Authorization failed (401). Token might be expired.")
        elif response.status_code == 403:
            print(f"\n[FAILED] Forbidden (403). Possible reasons:")
            print(" - You do not own Minecraft on this account.")
            print(" - You changed your name within the last 30 days.")
            print(" - The name was taken milliseconds ago.")
        elif response.status_code == 429:
            print(f"\n[FAILED] Rate Limited (429). Too many requests.")
        elif response.status_code == 400:
            print(f"\n[FAILED] Bad Request (400). Name might be invalid length/chars.")
        else:
            print(f"\n[FAILED] Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n[ERROR] Connection error: {e}")
    
    return False

def browse_and_claim(token):
    """Menu to browse found names by folder/file and claim them."""
    base_dir = "scans"
    if not os.path.exists(base_dir):
        print("No 'scans' folder found. Go find some names first!")
        input("Press Enter to return...")
        return

    while True:
        clear_screen()
        print("\n--- Sniper Mode: Select Category ---")
        
        # Level 1: Folders (Character Lengths)
        folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        folders.sort() # e.g. 3_characters, 4_characters
        
        if not folders:
            print("No scan folders found.")
            input("Press Enter to return...")
            return

        for i, folder in enumerate(folders):
            print(f"{i+1}. {folder}")
        
        print("\nType number to select, or 'b' to go back to Main Menu.")
        choice = input("Choice: ").strip().lower()
        
        if choice == 'b': return
        
        try:
            folder_idx = int(choice) - 1
            if 0 <= folder_idx < len(folders):
                selected_folder = folders[folder_idx]
                folder_path = os.path.join(base_dir, selected_folder)
                
                # Level 2: Files (Scan Modes)
                while True:
                    clear_screen()
                    print(f"\n--- Viewing: {selected_folder} ---")
                    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
                    files.sort()
                    
                    if not files:
                        print("No result files in this folder.")
                        input("Press Enter to go back...")
                        break

                    for i, f in enumerate(files):
                        print(f"{i+1}. {f}")
                    
                    print("\nType number to select file, or 'b' to go back.")
                    file_choice = input("Choice: ").strip().lower()
                    
                    if file_choice == 'b': break
                    
                    try:
                        file_idx = int(file_choice) - 1
                        if 0 <= file_idx < len(files):
                            selected_file = files[file_idx]
                            file_path = os.path.join(folder_path, selected_file)
                            
                            # Level 3: Names
                            while True:
                                clear_screen()
                                print(f"\n--- Available Names in {selected_file} ---")
                                available_names = []
                                try:
                                    with open(file_path, "r", encoding="utf-8") as f:
                                        for line in f:
                                            if "[AVAILABLE]" in line:
                                                name = line.split(" [")[0].strip()
                                                available_names.append(name)
                                except: pass
                                
                                if not available_names:
                                    print("No [AVAILABLE] names found in this file.")
                                    print("(Or they have already been claimed/marked taken)")
                                else:
                                    for i, name in enumerate(available_names):
                                        print(f"{i+1}. {name}")
                                
                                print("\nType number to CLAIM, or 'b' to go back.")
                                name_choice = input("Choice: ").strip().lower()
                                
                                if name_choice == 'b': break
                                
                                try:
                                    name_idx = int(name_choice) - 1
                                    if 0 <= name_idx < len(available_names):
                                        target_name = available_names[name_idx]
                                        print(f"\nAre you sure you want to change your IGN to '{target_name}'?")
                                        confirm = input("Type 'YES' to confirm: ").strip()
                                        
                                        if confirm == "YES":
                                            if claim_name(target_name, token):
                                                # Mark as claimed in file
                                                try:
                                                    with open(file_path, "r") as f: lines = f.readlines()
                                                    with open(file_path, "w") as f:
                                                        for line in lines:
                                                            if target_name in line:
                                                                f.write(line.replace("[AVAILABLE]", "[CLAIMED BY YOU]"))
                                                            else:
                                                                f.write(line)
                                                except: pass
                                                input("\nPress Enter to continue...")
                                        else:
                                            print("Cancelled.")
                                            time.sleep(1)
                                    else:
                                        print("Invalid number.")
                                        time.sleep(1)
                                except ValueError:
                                    print("Invalid input.")
                                    time.sleep(1)
                        else:
                            print("Invalid file number.")
                            time.sleep(1)
                    except ValueError:
                        print("Invalid input.")
                        time.sleep(1)
            else:
                print("Invalid folder number.")
                time.sleep(1)
        except ValueError:
            print("Invalid input.")
            time.sleep(1)


def delete_results():
    """Hierarchical menu to delete scan results."""
    base_dir = "scans"
    if not os.path.exists(base_dir):
        print("No 'scans' folder found.")
        input("Press Enter to return...")
        return

    while True:
        clear_screen()
        print("\n--- Delete Results: Select Folder ---")
        folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        folders.sort()
        
        if not folders:
            print("No folders found.")
            input("Press Enter to return...")
            return

        for i, folder in enumerate(folders):
            print(f"{i+1}. {folder}")
        
        print("\nType number to select, 'ALL' to delete everything, or 'b' to go back.")
        choice = input("Choice: ").strip().lower()
        
        if choice == 'b': return
        if choice == 'all':
            confirm = input("ARE YOU SURE? This wipes ALL scan results. (Type 'DELETE ALL'): ")
            if confirm == "DELETE ALL":
                import shutil
                shutil.rmtree(base_dir)
                os.makedirs(base_dir)
                print("Everything wiped.")
                time.sleep(1)
                return
            continue

        try:
            folder_idx = int(choice) - 1
            if 0 <= folder_idx < len(folders):
                selected_folder = folders[folder_idx]
                folder_path = os.path.join(base_dir, selected_folder)
                
                while True:
                    clear_screen()
                    print(f"\n--- Delete from: {selected_folder} ---")
                    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
                    files.sort()
                    
                    if not files:
                        print("Folder is empty.")
                        input("Press Enter to go back...")
                        break

                    for i, f in enumerate(files):
                        print(f"{i+1}. {f}")
                    
                    print("\nType number to DELETE file, 'FOLDER' to delete entire folder, or 'b' to go back.")
                    file_choice = input("Choice: ").strip().lower()
                    
                    if file_choice == 'b': break
                    if file_choice == 'folder':
                        confirm = input(f"Confirm deleting folder '{selected_folder}'? (y/n): ").lower()
                        if confirm == 'y':
                            import shutil
                            shutil.rmtree(folder_path)
                            print("Folder deleted.")
                            time.sleep(1)
                            break
                        continue

                    try:
                        file_idx = int(file_choice) - 1
                        if 0 <= file_idx < len(files):
                            target_file = files[file_idx]
                            file_path = os.path.join(folder_path, target_file)
                            confirm = input(f"Delete '{target_file}'? (y/n): ").lower()
                            if confirm == 'y':
                                os.remove(file_path)
                                print("File deleted.")
                                time.sleep(1)
                        else:
                            print("Invalid file number.")
                            time.sleep(1)
                    except ValueError:
                        print("Invalid input.")
                        time.sleep(1)
            else:
                print("Invalid folder number.")
                time.sleep(1)
        except ValueError:
            print("Invalid input.")
            time.sleep(1)

def filter_results():
    """Analyzes found names to find real words and 'leet' words."""
    base_dir = "scans"
    if not os.path.exists(base_dir):
        print("No scans found.")
        input("Press Enter...")
        return

    # Load dictionary for checking
    print("Loading dictionary for analysis...")
    vocab = set()
    if os.path.exists(WORDLIST_FILE):
        with open(WORDLIST_FILE, "r") as f:
            for line in f:
                vocab.add(line.strip().lower())
    else:
        print("Dictionary file missing. Cannot filter.")
        return

    # Leet map
    # 0->o, 1->i, 3->e, 4->a, 5->s, 7->t
    leet_map = str.maketrans("013457", "oieast")

    clean_words = []
    leet_words = []
    
    # Collect all AVAILABLE names
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
                                
                                # Check 1: Is it a clean word?
                                if name in vocab:
                                    clean_words.append(name)
                                    continue
                                
                                # Check 2: Is it a leet word?
                                de_leeted = name.translate(leet_map)
                                if de_leeted != name and de_leeted in vocab:
                                    leet_words.append(f"{name} ({de_leeted})")
                except: pass

    clear_screen()
    print(f"--- Analysis Complete (Scanned {total_found} names) ---")
    print(f"Found {len(clean_words)} Clean Dictionary Words.")
    print(f"Found {len(leet_words)} Leet-Speak Words.\n")
    
    if clean_words:
        print("--- CLEAN WORDS ---")
        for i in range(0, len(clean_words), 25):
            chunk = clean_words[i:i+25]
            print(", ".join(chunk))
            if i + 25 < len(clean_words):
                input("\nPress Enter for more...")
        print("\n")

    if leet_words:
        print("--- LEET WORDS ---")
        for i in range(0, len(leet_words), 25):
            chunk = leet_words[i:i+25]
            print(", ".join(chunk))
            if i + 25 < len(leet_words):
                input("\nPress Enter for more...")
    
    input("\nPress Enter to return to menu...")

def main():
    print("--- Minecraft IGN Scanner ---")

    # Get authentication
    bearer_token = prompt_bearer_token()

    if not bearer_token:
        print("Authentication failed. Exiting.")
        return

    # Outer loop to return to Main Menu after scanning
    while True:
        clear_screen()
        print("\n=== Main Menu ===")
        print("1. Start Scanner")
        print("2. Sniper Mode (Browse & Claim)")
        print("3. Clear Results")
        print("4. Filter & Organize Results")
        print("5. Exit")
        
        main_choice = input("Choice: ").strip()
        
        if main_choice == "5":
            print("Goodbye!")
            return
        elif main_choice == "4":
            filter_results()
            continue
        elif main_choice == "3":
            delete_results()
            continue
        elif main_choice == "2":
            browse_and_claim(bearer_token)
            continue
        elif main_choice == "1":
            # Proceed to scanner setup
            break 
        else:
            print("Invalid choice.")
            time.sleep(1)
            continue

        # --- Scanner Setup (Option 1) ---
        clear_screen()
        # 1. Input Length
    while True:
        try:
            char_limit_input = input("\nEnter character limit (3-16): ")
            char_limit = int(char_limit_input)
            if 3 <= char_limit <= 16:
                break
            print("Invalid length.")
        except ValueError:
            print("Invalid input.")

    # 2. Input Mode
    mode = "random"
    word_list = []
    print("\nSelect generation mode:")
    print("1. Random (e.g. 'x9_k2')")
    print("2. Dictionary Words (All ~370k words)")
    print("3. Common Words (Top ~10k words)")
    
    while True:
        mode_input = input("Choice (1, 2, or 3): ").strip()
        if mode_input == "1":
            mode = "random"
            break
        elif mode_input == "2":
            mode = "dictionary"
            print("Loading full dictionary...")
            word_list = load_words(char_limit, WORDLIST_FILE)
            if not word_list:
                print(f"No words found for length {char_limit}. Defaulting to Random.")
                mode = "random"
            else:
                print(f"Loaded {len(word_list)} words of length {char_limit} from full dictionary.")
            break
        elif mode_input == "3":
            mode = "common_words"
            print("Loading common words list...")
            word_list = load_words(char_limit, COMMON_WORDS_FILE)
            if not word_list:
                print(f"No common words found for length {char_limit}. Defaulting to Random.")
                mode = "random"
            else:
                print(f"Loaded {len(word_list)} common words of length {char_limit}.")
            break
        else:
            print("Invalid choice.")

    # 3. Input Count
    target_count = float('inf')
    while True:
        count_input = input("\nEnter number of names to check (Press Enter for infinite): ")
        if not count_input.strip():
            break
        try:
            count = int(count_input)
            if count > 0:
                target_count = count
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input.")

    # Organized Folder Structure: scans/3_characters/3_characters_ign_random.txt
    output_dir = f"scans/{char_limit}_characters"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f"{output_dir}/{char_limit}_characters_ign_{mode}.txt"
    
    # Load Blacklist, Locked List, and Proxies
    blacklisted_names = load_blacklist()
    locked_names = load_locked_list()
    global PROXY_LIST
    PROXY_LIST = load_proxies()
    
    # Smart Resume: Load names we already found in this file
    already_found = load_existing_results(filename)
    
    if locked_names:
        skip_locked = input(f"Skip {len(locked_names)} known locked accounts to save time? (y/n): ").strip().lower()
        if skip_locked == 'y':
            print("Skipping locked accounts.")
            blacklisted_names.update(locked_names)
        else:
            print("Re-checking locked accounts (they will be removed from the list if found free).")
    
    # Filter word list if using dictionary modes
    if mode in ["dictionary", "common_words"]:
        original_len = len(word_list)
        word_list = [w for w in word_list if w.lower() not in already_found]
        if len(word_list) < original_len:
            print(f"Skipping {original_len - len(word_list)} names already in results file.")
        
        random.shuffle(word_list)
        print("Shuffled word list for unique coverage.")
    else:
        # For random mode, treat existing results as blacklisted
        blacklisted_names.update(already_found)

    try:
        # Open in append mode so we don't lose previous results
        file_exists = os.path.exists(filename)
        # We no longer write headers/resume labels to keep the list clean
        print(f"\nResults will be saved/appended to: {filename}")
        
    except IOError:
        print("Error accessing file.")
        return

    clear_screen()
    print("--- Scan Configuration ---")
    print(f"Target Length: {char_limit} characters")
    print(f"Mode: {mode.replace('_', ' ').title()}")
    count_display = "Infinite" if target_count == float('inf') else target_count
    if mode != "random":
        count_display = f"{len(word_list)} remaining words"
    print(f"Target Count: {count_display}")
    print(f"Saving to: {filename}")
    print("--------------------------")
    print("\nStarting scan... (Press Ctrl+C to stop)\n")

    # Pre-load stats from existing data
    total_available = len(already_found)
    total_unavailable = 0
    
    # Only count locked/blocked names that match the current character length
    total_not_allowed = len([n for n in blacklisted_names if len(n) == char_limit])
    total_locked = len([n for n in locked_names if len(n) == char_limit])
    
    total_unverified = 0
    auth_valid = True
    batch_size = 10
    names_since_pause = 0

    def update_display(final=False):
        scanned = total_available + total_unavailable + total_not_allowed + total_locked + total_unverified
        
        # Calculate remaining
        if mode == "random":
            remaining = "Infinite"
        else:
            remaining = len(word_list)

        line = (f"Scanned: {scanned} | Available: {total_available}"
                f" | Taken: {total_unavailable} | Locked: {total_locked}"
                f" | Blocked: {total_not_allowed} | Remaining: {remaining}")
        
        # \r to return to start, \x1b[2K to clear the line
        sys.stdout.write(f"\r\x1b[2K{line}")
        if final:
            sys.stdout.write("\n")
        sys.stdout.flush()

    try:
        processed_count = 0
        while processed_count < target_count:
            try:
                # Determine batch size
                current_batch_size = batch_size
                if target_count != float('inf'):
                    remaining = int(target_count - processed_count)
                    if remaining < batch_size:
                        current_batch_size = remaining

                if current_batch_size <= 0:
                    break

                # Generate Names
                batch_names = set()
                attempts = 0
                max_attempts = current_batch_size * 100 

                while len(batch_names) < current_batch_size:
                    name = ""
                    if mode in ["dictionary", "common_words"]:
                         if not word_list:
                             break
                         # Take the last word from the shuffled list
                         name = word_list.pop()
                    else:
                        name = generate_random_name(char_limit)

                    if name.lower() in blacklisted_names:
                        # For dictionary mode, if it's blacklisted, it's already popped. 
                        # We just move to the next.
                        attempts += 1
                        if attempts > max_attempts: break
                        continue

                    batch_names.add(name)
                    attempts += 1
                    if attempts > max_attempts: break

                if not batch_names:
                    print("\nCould not generate more unique names.")
                    break

                batch_list = list(batch_names)
                processed_count += len(batch_list)

                # Stage 1: Bulk check (unauthenticated)
                taken_names_set, failed_names_set = check_names_bulk(batch_list)

                candidates = []
                for name in batch_list:
                    if name in failed_names_set:
                        candidates.append(name)
                        continue

                    is_taken = False
                    for taken in taken_names_set:
                        if taken.lower() == name.lower():
                            total_unavailable += 1
                            is_taken = True
                            break

                    if not is_taken:
                        candidates.append(name)
                    else:
                        update_display()

                # Stage 2: Unauthenticated individual verify (Multi-threaded)
                stage2_candidates = []
                
                # Helper for threading
                def verify_wrapper(name):
                    res = verify_name(name)
                    return name, res

                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    # Submit all candidates
                    future_to_name = {executor.submit(verify_wrapper, n): n for n in candidates}
                    
                    # Process as they complete
                    for future in concurrent.futures.as_completed(future_to_name):
                        name, result = future.result()
                        if result == "available":
                            stage2_candidates.append(name)
                        elif result == "taken":
                            total_unavailable += 1
                        else:
                            total_unverified += 1
                        
                        update_display()

                # Stage 3: Authenticated status check
                if auth_valid:
                    for name in stage2_candidates:
                        status = check_name_status(name, bearer_token)
                        
                        res_status = ""
                        if status == "AVAILABLE":
                            total_available += 1
                            res_status = "AVAILABLE"
                            
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
                            # Do NOT write to scan file (res_status left empty)
                            # Only add to the master Locked_IGNs.txt list
                            if name.lower() not in locked_names:
                                locked_names.add(name.lower())
                                append_to_locked_list(name)
                                
                        elif status == "AUTH_EXPIRED":
                            sys.stdout.write("\n")
                            print("Bearer token expired!")
                            auth_valid = False
                            total_unverified += 1
                        else:
                            total_unverified += 1

                        if res_status:
                            try:
                                with open(filename, "a") as f:
                                    f.write(f"{name} [{res_status}]\n")
                            except IOError: pass

                        update_display()
                        time.sleep(0.5)

                # Cooling down logic
                names_since_pause += len(batch_list)
                if names_since_pause >= 50:
                    # Clear line and print cooling message
                    sys.stdout.write(f"\r\x1b[2KScanned: {total_available+total_unavailable+total_not_allowed+total_locked+total_unverified} ... [PAUSED] Cooling down 3s...")
                    sys.stdout.flush()
                    time.sleep(3)
                    update_display()
                    names_since_pause = 0

            except KeyboardInterrupt:
                # Pause and ask
                sys.stdout.write("\n\n[PAUSED] Scan interrupted.\n")
                choice = input("Quit to Main Menu? (y/n): ").strip().lower()
                if choice == 'y':
                    break
                else:
                    print("Resuming scan...")
                    update_display()
                    continue

    except KeyboardInterrupt:
        print("\n\nScan stopped by user.")

    # Final Summary before returning to menu
    update_display(final=True)
    print("\nProcess finished.")
    print(f"Total processed: {total_available+total_unavailable+total_not_allowed+total_locked+total_unverified}")
    print(f"Available: {total_available}")
    print(f"Taken: {total_unavailable}")
    print(f"Locked (recorded): {total_locked}")
    print(f"Blocked by filter: {total_not_allowed}")
    print(f"Could not verify: {total_unverified}")
    print(f"Results saved to {filename}")
    input("\nPress Enter to return to the Main Menu...")

if __name__ == "__main__":
    main()
