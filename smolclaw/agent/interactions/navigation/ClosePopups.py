"""Close popups interaction."""

from helium import press
from selenium.webdriver.common.keys import Keys


class ClosePopups:
    @staticmethod
    def execute() -> str:
        """Closes any visible modal or pop-up by pressing ESC."""
        press(Keys.ESCAPE)
        return "Pressed ESC key to close popups"
