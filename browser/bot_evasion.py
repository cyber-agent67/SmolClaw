"""Anti-detection arguments for browser automation."""

BOT_EVASION_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-background-timer-throttling",
    "--disable-popup-blocking",
    "--no-first-run",
    "--no-default-browser-check",
]

EVASION_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
"""
