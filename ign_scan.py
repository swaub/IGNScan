import requests
import random
import string
import time
import sys
import os

# URL for a standard English word list
WORDLIST_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
WORDLIST_FILE = "words_alpha.txt"

def download_wordlist():
    """Downloads a word list if not already present."""
    if not os.path.exists(WORDLIST_FILE):
        print("Downloading dictionary file (this may take a moment)...")
        try:
            response = requests.get(WORDLIST_URL)
            response.raise_for_status()
            with open(WORDLIST_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Dictionary downloaded successfully.")
        except Exception as e:
            print(f"Failed to download dictionary: {e}")
            return False
    return True

def load_words(length):
    """Loads words of a specific length from the word list."""
    if not download_wordlist():
        return []
    
    valid_words = []
    try:
        with open(WORDLIST_FILE, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if len(word) == length:
                    valid_words.append(word)
    except Exception:
        pass
    return valid_words

def generate_random_name(length):
    chars = string.ascii_letters + string.digits + '_'
    return ''.join(random.choice(chars) for _ in range(length))

def check_names_bulk(names):
    url = "https://api.mojang.com/profiles/minecraft"
    taken_names = set()
    # Mojang API allows up to 10 names per request
    chunks = [names[i:i + 10] for i in range(0, len(names), 10)]
    
    for chunk in chunks:
        try:
            response = requests.post(url, json=chunk, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                data = response.json()
                for profile in data:
                    taken_names.add(profile['name'])
            elif response.status_code == 429:
                # Rate limited
                time.sleep(5)
                retry_response = requests.post(url, json=chunk, headers={"Content-Type": "application/json"})
                if retry_response.status_code == 200:
                    data = retry_response.json()
                    for profile in data:
                        taken_names.add(profile['name'])
            
            # Small delay to respect API limits
            time.sleep(0.1)
            
        except Exception:
            pass

    return taken_names

def main():
    print("--- Minecraft IGN Scanner ---")
    
    # 1. Input Length
    while True:
        try:
            char_limit_input = input("Enter character limit (3-16): ")
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
    print("2. Dictionary Words (e.g. 'apple')")
    
    while True:
        mode_input = input("Choice (1 or 2): ").strip()
        if mode_input == "1":
            mode = "random"
            break
        elif mode_input == "2":
            mode = "dictionary"
            print("Loading dictionary...")
            word_list = load_words(char_limit)
            if not word_list:
                print(f"No words found for length {char_limit} or download failed. Defaulting to Random.")
                mode = "random"
            else:
                print(f"Loaded {len(word_list)} words of length {char_limit}.")
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

    filename = f"{char_limit}_characters_ign.txt"
    
    try:
        with open(filename, "w") as f:
            f.write(f"--- Available Results for {char_limit} char names ({mode}) ---\n")
            f.write(f"Scan started at {time.ctime()}\n\n")
        print(f"\nAvailable names will be saved to: {filename}")
        
    except IOError:
        print("Error creating file.")
        return

    print("\nStarting scan... (Press Ctrl+C to stop)")

    generated_count = 0
    total_available = 0
    total_unavailable = 0
    batch_size = 10
    
    try:
        while generated_count < target_count:
            # Determine batch size
            current_batch_size = batch_size
            if target_count != float('inf'):
                remaining = int(target_count - generated_count)
                if remaining < batch_size:
                    current_batch_size = remaining
            
            if current_batch_size <= 0:
                break

            # Generate Names
            batch_names = set()
            attempts = 0
            # Safety break for dictionary mode if we run out of words
            max_attempts = current_batch_size * 10 
            
            while len(batch_names) < current_batch_size:
                if mode == "dictionary":
                     # In dictionary mode, we just pick random words from the loaded list
                     if not word_list:
                         break 
                     batch_names.add(random.choice(word_list))
                else:
                    batch_names.add(generate_random_name(char_limit))
                
                attempts += 1
                if attempts > max_attempts:
                    break
            
            if not batch_names:
                print("\nCould not generate more unique names (maybe dictionary exhausted?).")
                break

            batch_list = list(batch_names)
            
            # Check batch
            taken_names_set = check_names_bulk(batch_list)
            
            available = []
            unavailable = []

            for name in batch_list:
                is_taken = False
                for taken in taken_names_set:
                    if taken.lower() == name.lower():
                        unavailable.append(name)
                        is_taken = True
                        break
                
                if not is_taken:
                    available.append(name)

            # Update stats
            total_available += len(available)
            total_unavailable += len(unavailable)
            generated_count += len(batch_list)

            # Append results to file (Only Available ones)
            if available:
                try:
                    with open(filename, "a") as f:
                        for name in available:
                            f.write(f"{name}\n")
                except IOError:
                    pass

            # Print Status (Single updating line)
            # \r returns cursor to start of line, end="" prevents new line
            sys.stdout.write(f"\rScanned: {generated_count} | Available: {total_available} | Taken: {total_unavailable}")
            sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("\n\nScan stopped by user.")

    print(f"\n\nScan complete.")
    print(f"Total processed: {generated_count}")
    print(f"Total Available found: {total_available}")
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()
