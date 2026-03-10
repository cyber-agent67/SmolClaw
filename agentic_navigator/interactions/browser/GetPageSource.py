"""Get page source interaction."""

from helium import get_driver


class GetPageSource:
    @staticmethod
    def execute() -> str:
        """Gets the raw HTML source of the current page."""
        driver = get_driver()
        return driver.page_source
