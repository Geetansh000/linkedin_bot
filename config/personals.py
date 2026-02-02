from dotenv import load_dotenv
import os
load_dotenv()

# Your LinkedIn credentials
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
SEARCH_STRING = os.getenv("SEARCH_STRING")
your_name = os.getenv("NAME")
years_of_experience = os.getenv("YEARS_OF_EXPERIENCE")
resume_link = os.getenv("RESUME_LINK")
portfolio_link = os.getenv("PORTFOLIO_LINK")
skip_words = list(map(str.strip, os.getenv("SKIP_WORDS", "").split(
    ","))) if os.getenv("SKIP_WORDS", "") else []

connection_start = None
connection_end = None
