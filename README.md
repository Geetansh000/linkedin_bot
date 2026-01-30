# LinkedIn Follow Automation

This project automates LinkedIn login and messaging using Selenium and undetected-chromedriver.

## Features
- Automated login (guest profile, no history saved)
- Automated messaging
- Handles ChromeDriver and Chrome version compatibility
- Logs and screenshots for debugging

## Requirements
- Python 3.12+
- Google Chrome (version must match ChromeDriver)
- See requirements.txt for Python dependencies

## Setup
1. Clone the repository or download the code.
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Ensure your Chrome version matches the ChromeDriver version. If you see errors about version mismatch, update Chrome or set the correct ChromeDriver version.

## Usage
Run the login script:
```bash
python login.py
```

## Troubleshooting
- **ChromeDriver version mismatch:**
  - Update Chrome or set the environment variable `UCD_CHROMEDRIVER_VERSION` to match your Chrome version.
- **Unicode/BMP error:**
  - Only use standard characters and emojis in messages.
- **Too many tabs open:**
  - Close or bookmark tabs before running the script.

## Project Structure
- `login.py`, `message.py`: Main scripts
- `modules/`: Helper modules for browser automation
- `config/`: Configuration files
- `logs/`: Log files and screenshots

## License
MIT License
