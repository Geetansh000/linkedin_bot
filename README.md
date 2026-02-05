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

### Run the main entry point:
```bash
python -m linkedIn_follow
```

### Or run specific scripts:
```bash
python -m linkedIn_follow.scripts.login
python -m linkedIn_follow.scripts.connections
python -m linkedIn_follow.scripts.message
```

### After installation with pip:
```bash
linkedin-follow
```

## Project Structure
```
linkedIn_follow/
├── __init__.py                  # Package initialization
├── __main__.py                  # Entry point for python -m
├── config/                      # Configuration package
│   ├── __init__.py
│   ├── personals.py            # Personal settings (credentials, preferences)
│   ├── settings.py             # Global settings
│   └── text.py                 # Message templates
├── modules/                     # Helper modules
│   ├── __init__.py
│   ├── open_chrome.py          # Chrome/Selenium initialization
│   ├── helpers.py              # Utility functions
│   ├── clickers_and_finders.py # Element interaction functions
│   └── validator.py            # Configuration validation
├── scripts/                     # Script entry points
│   ├── __init__.py
│   ├── main.py                 # Main entry point
│   ├── login.py                # Login automation
│   ├── connections.py          # Connection finding
│   └── message.py              # Message sending
├── logs/                        # Log files and history
└── templates/                   # HTML templates (if needed)

setup.py                         # Setup configuration for pip
pyproject.toml                   # Project metadata
requirements.txt                 # Python dependencies
.env.example                     # Example environment variables
.gitignore                       # Git ignore rules
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your LinkedIn credentials:
   ```
   LINKEDIN_USERNAME=your@email.com
   LINKEDIN_PASSWORD=your_password
   SEARCH_STRING=Backend Developer
   NAME=Your Name
   YEARS_OF_EXPERIENCE=5
   RESUME_LINK=https://drive.google.com/...
   PORTFOLIO_LINK=https://yourportfolio.com
   ```

3. Update settings in `linkedIn_follow/config/settings.py` if needed

## Troubleshooting
- **ChromeDriver version mismatch:**
  - Update Chrome or set the environment variable `UCD_CHROMEDRIVER_VERSION` to match your Chrome version.
- **Unicode/BMP error:**
  - Only use standard characters and emojis in messages.
- **Too many tabs open:**
  - Close or bookmark tabs before running the script.
- **Module import errors:**
  - Ensure you're running from the project root directory
  - Install the package: `pip install -e .`

## License
MIT License
