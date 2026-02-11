# IGNScan

A Minecraft In-Game Name (IGN) scanner that finds and claims available usernames using the Mojang and Minecraft Services APIs.

## Features

- **3 Scan Modes** — Random strings, full dictionary (~370k words), or common words (~10k words)
- **3-Stage Verification** — Bulk API check, individual verification, then authenticated confirmation to ensure accuracy
- **Auto Token Grab** — Opens a browser and captures your Minecraft Bearer token automatically via Selenium (supports Chrome and Edge)
- **Sniper Mode** — Browse found names and claim them directly to your account, with re-verification before claiming
- **Proxy Support** — Rotate through proxies from `proxies.txt` to avoid rate limiting
- **Live Progress** — Real-time stats, scan speed, ETA, and instant notifications when available names are found
- **Smart Resume** — Skips already-scanned names when restarting a dictionary/common words scan
- **Auto-Management** — Automatically blacklists blocked names and tracks locked/duplicate names

## Quick Start

```bash
# Clone the repo
git clone https://github.com/swaub/IGNScan.git
cd IGNScan

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows (CMD)
venv\Scripts\Activate.ps1   # Windows (PowerShell)
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run
python ign_scan.py
```

On first launch, choose **Auto** to open a browser and grab your Minecraft token automatically, or **Manual** to paste one in. See [SETUP.md](SETUP.md) for detailed instructions on getting a Bearer token.

## How It Works

1. **Authenticate** — Your Minecraft Bearer token is used for accurate name availability checks
2. **Generate** — Names are generated based on your chosen mode and character length (3-16)
3. **Verify** — Each name goes through bulk check, individual API verification, and authenticated status check
4. **Save** — Available names are saved to `scans/` organized by character length
5. **Claim** — Use Sniper Mode to browse results and claim names directly to your account

## File Structure

| File | Description |
|------|-------------|
| `ign_scan.py` | Main scanner application |
| `SETUP.md` | Detailed setup and usage guide |
| `requirements.txt` | Python dependencies |
| `proxies.txt` | Your proxy list (optional, create manually) |
| `token.txt` | Saved Bearer token (auto-created, gitignored) |
| `scans/` | Scan results organized by character length |
| `blacklisted_words.txt` | Auto-managed list of blocked names |
| `Locked_IGNs.txt` | Auto-managed list of duplicate/locked names |

## Requirements

- Python 3.8+
- Google Chrome or Microsoft Edge (for auto token grab)
- A Minecraft Java Edition account

## License

This project is for educational purposes only. Use responsibly and respect Mojang's API rate limits.
