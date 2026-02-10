import requests
import random
import string
import time
import sys
import os
import concurrent.futures

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
    "Sec-Fetch-Site": "cross-site"
}

PROXY_LIST = []

# --- Helper Functions ---

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_session():
    sess = requests.Session()
    sess.headers.update(HEADERS)
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        sess.proxies = {"http": proxy, "https": proxy}
    return sess

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
            if proxies: print(f"Loaded {len(proxies)} proxies.")
        except: pass
    return proxies

def load_blacklist():
    blacklisted = set()
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip().lower()
                    if name: blacklisted.add(name)
        except: pass
    return blacklisted

def append_to_blacklist(name):
    try:
        with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
    except: pass

def load_locked_list():
    locked = set()
    if os.path.exists(LOCKED_FILE):
        try:
            with open(LOCKED_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip().lower()
                    if name: locked.add(name)
        except: pass
    return locked

def append_to_locked_list(name):
    try:
        with open(LOCKED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
    except: pass

def remove_from_locked_list(name, current_set):
    if name.lower() in current_set:
        current_set.remove(name.lower())
        try:
            with open(LOCKED_FILE, "w", encoding="utf-8") as f:
                for n in current_set: f.write(f"{n}\n")
        except: pass

def load_existing_results(filename):
    found = set()
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    if " [" in line:
                        found.add(line.split(" [")[0].strip().lower())
        except: pass
    return found

def download_file(url, filename, description="file"):
    if not os.path.exists(filename):
        print(f"Downloading {description}...")
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            with open(filename, "w", encoding="utf-8") as f: f.write(r.text)
            print(f"{description} downloaded.")
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    return True

def load_words(length, source_file):
    if not download_file(WORDLIST_URL if source_file == WORDLIST_FILE else COMMON_WORDS_URL, source_file):
        return []
    valid = []
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if len(word) == length: valid.append(word)
    except: pass
    return valid

def generate_random_name(length):
    chars = string.ascii_lowercase + string.digits + '_'
    return ''.join(random.choice(chars) for _ in range(length))

def parse_duration(d_str):
    if not d_str: return None
    try:
        unit = d_str[-1].lower()
        val = int(d_str[:-1])
        return val * {"s":1, "m":60, "h":3600, "d":86400}.get(unit, 0)
    except: return None

# --- API Interaction ---

def check_names_bulk(names):
    url = "https://api.mojang.com/profiles/minecraft"
    taken, failed = set(), set()
    chunks = [names[i:i + 10] for i in range(0, len(names), 10)]
    for chunk in chunks:
        while True:
            s = get_session()
            try:
                r = s.post(url, json=chunk, timeout=10)
                if r.status_code == 200:
                    for p in r.json(): taken.add(p['name'])
                    break
                elif r.status_code == 429:
                    time.sleep(10)
                    continue
                else:
                    failed.update(chunk)
                    break
            except: 
                time.sleep(10)
        time.sleep(random.uniform(1.5, 2.5))
    return taken, failed

def verify_name(name):
    url = f"https://api.mojang.com/users/profiles/minecraft/{name}"
    while True:
        s = get_session()
        try:
            r = s.get(url, timeout=10)
            if r.status_code == 200: return "taken"
            if r.status_code in [404, 204]: return "available"
            if r.status_code == 429:
                time.sleep(10)
                continue
            return "unknown"
        except: time.sleep(10)

def check_name_status(name, token):
    url = f"https://api.minecraftservices.com/minecraft/profile/name/{name}/available"
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    while True:
        s = get_session()
        try:
            r = s.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                time.sleep(8) # Throttle
                return r.json().get("status", "unknown")
            if r.status_code == 401: return "AUTH_EXPIRED"
            if r.status_code == 429:
                time.sleep(10)
                continue
            return "unknown"
        except: time.sleep(10)

def claim_name(name, token):
    url = f"https://api.minecraftservices.com/minecraft/profile/name/{name}"
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.put(url, headers=headers, timeout=15)
        if r.status_code == 200:
            print(f"\n[!!!] SUCCESS! Claimed: {name}")
            return True
        print(f"\n[FAILED] {r.status_code}: {r.text}")
    except Exception as e: print(f"\n[ERROR] {e}")
    return False

# --- UI Menus ---

def prompt_bearer_token():
    print("\n--- Authentication ---")
    print("Please enter your Bearer Token. (See SETUP.md for help)")
    while True:
        if os.path.exists("token.txt"):
            with open("token.txt", "r") as f: token = f.read().strip()
            print("Loaded token from token.txt")
        else:
            token = input("Paste Token: ").strip()
        if not token: continue
        print("Validating...")
        status = check_name_status("Notch", token)
        if status in ["TAKEN", "DUPLICATE", "AVAILABLE", "NOT_ALLOWED"]:
            with open("token.txt", "w") as f: f.write(token)
            return token
        print(f"Invalid token ({status}).")
        if os.path.exists("token.txt"): os.remove("token.txt")
        if input("Try again? (y/n): ").lower() != 'y': return None

def browse_and_claim(token):
    if not os.path.exists("scans"): return print("No scans found.")
    while True:
        clear_screen()
        folders = sorted([d for d in os.listdir("scans") if os.path.isdir(os.path.join("scans", d))])
        if not folders: return print("No folders found.")
        for i, f in enumerate(folders): print(f"{i+1}. {f}")
        c = input("\nSelect folder (or 'b'): ").lower()
        if c == 'b': break
        try:
            fld = folders[int(c)-1]
            fld_path = os.path.join("scans", fld)
            while True:
                clear_screen()
                files = sorted([f for f in os.listdir(fld_path) if f.endswith(".txt")])
                for i, f in enumerate(files): print(f"{i+1}. {f}")
                fc = input("\nSelect file (or 'b'): ").lower()
                if fc == 'b': break
                path = os.path.join(fld_path, files[int(fc)-1])
                while True:
                    clear_screen()
                    names = []
                    with open(path, "r") as f:
                        for line in f:
                            if "[AVAILABLE]" in line: names.append(line.split(" [")[0].strip())
                    if not names:
                        print("No available names."); input("Press Enter..."); break
                    for i, n in enumerate(names): print(f"{i+1}. {n}")
                    nc = input("\nNumber to CLAIM (or 'b'): ").lower()
                    if nc == 'b': break
                    target = names[int(nc)-1]
                    if input(f"Claim '{target}'? (YES/n): ") == "YES":
                        if claim_name(target, token):
                            with open(path, "r") as f: lines = f.readlines()
                            with open(path, "w") as f:
                                for l in lines: f.write(l.replace("[AVAILABLE]", "[CLAIMED]"))
                            input("Press Enter...")
        except: pass

def delete_results():
    if not os.path.exists("scans"): return
    import shutil
    while True:
        clear_screen()
        folders = sorted([d for d in os.listdir("scans") if os.path.isdir(os.path.join("scans", d))])
        for i, f in enumerate(folders): print(f"{i+1}. {f}")
        c = input("\nDelete folder #, 'ALL', or 'b': ").lower()
        if c == 'b': break
        if c == 'all' and input("Wipe everything? (y/n): ") == 'y':
            shutil.rmtree("scans"); os.makedirs("scans"); return
        try:
            path = os.path.join("scans", folders[int(c)-1])
            if input(f"Delete {path}? (y/n): ") == 'y': shutil.rmtree(path)
        except: pass

def filter_results():
    vocab = set()
    if os.path.exists(WORDLIST_FILE):
        with open(WORDLIST_FILE, "r") as f:
            for line in f:
                vocab.add(line.strip().lower())
    leet_map = str.maketrans("013457", "oieast")
    clean, leet = [], []
    for root, _, files in os.walk("scans"):
        for file in files:
            if not file.endswith(".txt"): continue
            with open(os.path.join(root, file), "r") as f:
                for line in f:
                    if "[AVAILABLE]" in line:
                        name = line.split(" [")[0].strip().lower()
                        if name in vocab: clean.append(name)
                        else:
                            dl = name.translate(leet_map)
                            if dl in vocab: leet.append(f"{name} ({dl})")
    clear_screen()
    print(f"Found {len(clean)} Clean, {len(leet)} Leet.")
    if clean: print("\nClean:", ", ".join(clean[:50]))
    if leet: print("\nLeet:", ", ".join(leet[:50]))
    input("\nPress Enter...")

# --- Main Scan Engine ---

def run_scanner(token):
    clear_screen()
    try:
        limit = int(input("Length (3-16): "))
        print("\n1. Random\n2. Dictionary\n3. Common")
        m_idx = input("Choice: ")
        mode = { "1":"random", "2":"dictionary", "3":"common_words" }.get(m_idx, "random")
        word_list = load_words(limit, WORDLIST_FILE if mode=="dictionary" else COMMON_WORDS_FILE) if mode != "random" else []
        
        target_input = input("\nCount or Duration (e.g. 5000, 1h): ")
        t_seconds = parse_duration(target_input)
        t_count = int(target_input) if not t_seconds and target_input else float('inf')
        
        out_dir = f"scans/{limit}_characters"
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        filename = f"{out_dir}/{limit}_characters_ign_{mode}.txt"
        
        blacklist = load_blacklist()
        locked = load_locked_list()
        global PROXY_LIST
        PROXY_LIST = load_proxies()
        found = load_existing_results(filename)
        
        if mode != "random":
            word_list = [w for w in word_list if w.lower() not in found]
            random.shuffle(word_list)
        else: blacklist.update(found)

        clear_screen()
        print(f"--- Scan: {limit} chars | {mode} ---")
        start_t = time.time()
        
        av, unav, blk, lock = len(found), 0, len([n for n in blacklist if len(n)==limit]), len([n for n in locked if len(n)==limit])
        
        def display():
            scanned = av + unav + blk + lock
            rem = f"{int(t_seconds - (time.time()-start_t))}s" if t_seconds else (len(word_list) if mode!="random" else "Inf")
            sys.stdout.write(f"\r\x1b[2KScanned: {scanned} | Avail: {av} | Taken: {unav} | Rem: {rem}")
            sys.stdout.flush()

        p_count = 0
        while p_count < t_count:
            if t_seconds and (time.time()-start_t) >= t_seconds: break
            try:
                batch = []
                while len(batch) < 10:
                    name = word_list.pop() if word_list else (generate_random_name(limit) if mode=="random" else None)
                    if not name: break
                    if name.lower() in blacklist: blk += 1; continue
                    batch.append(name)
                if not batch: break
                
                p_count += len(batch)
                taken_set, failed = check_names_bulk(batch)
                
                candidates = []
                for n in batch:
                    if n in failed: candidates.append(n)
                    elif n.lower() in [t.lower() for t in taken_set]: unav += 1
                    else: candidates.append(n)
                display()

                stage2 = []
                def v_wrap(n): return n, verify_name(n)
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exe:
                    for fut in concurrent.futures.as_completed({exe.submit(v_wrap, n): n for n in candidates}):
                        n, res = fut.result()
                        if res == "available": stage2.append(n)
                        else: unav += 1
                        display()

                for n in stage2:
                    st = check_name_status(n, token)
                    if st == "AVAILABLE":
                        av += 1
                        with open(filename, "a") as f: f.write(f"{n} [AVAILABLE]\n")
                    elif st == "DUPLICATE":
                        lock += 1
                        if n.lower() not in locked: append_to_locked_list(n)
                    elif st == "NOT_ALLOWED":
                        blk += 1
                        if n.lower() not in blacklist: append_to_blacklist(n)
                    else: unav += 1
                    display()
                
                if p_count % 50 == 0: time.sleep(3) # Cooldown
            except KeyboardInterrupt:
                if input("\nQuit to Menu? (y/n): ") == 'y': break
        
        display(); print("\nFinished."); input("Enter to return...")
    except Exception as e: print(f"Error: {e}"); input("Enter...")

def main():
    token = prompt_bearer_token()
    if not token: return
    while True:
        clear_screen()
        print("\n=== IGN SCANNER ===\n1. Scan\n2. Sniper\n3. Delete\n4. Filter\n5. Exit")
        choice = input("Choice: ")
        if choice == "5": break
        if choice == "1": run_scanner(token)
        if choice == "2": browse_and_claim(token)
        if choice == "3": delete_results()
        if choice == "4": filter_results()

if __name__ == "__main__":
    main()