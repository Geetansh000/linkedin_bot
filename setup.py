from setuptools import setup, find_packages

setup(
    name="linkedIn_follow",
    version="0.1.0",
    description="Automate LinkedIn connection messaging and outreach.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "selenium==4.15.2",
        "python-dotenv==1.0.0",
        "webdriver-manager==4.0.1",
        "pyautogui==0.9.53",
        "undetected-chromedriver==3.5.5",
        "packaging==23.2",
    ],
    entry_points={
        "console_scripts": [
            "linkedin-follow=linkedIn_follow.scripts.main:run"
        ]
    },
    include_package_data=True,
    python_requires=">=3.7",
)
