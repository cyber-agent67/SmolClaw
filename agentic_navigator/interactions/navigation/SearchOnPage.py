"""Search on page interaction."""

from helium import get_driver
from selenium.webdriver.common.by import By


class SearchOnPage:
    @staticmethod
    def execute(text: str, nth_result: int = 1) -> str:
        """Searches for text on the current page and jumps to nth occurrence."""
        driver = get_driver()
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")

        if nth_result > len(elements):
            raise Exception(f"Match n{nth_result} not found (only {len(elements)} matches found)")

        result = f"Found {len(elements)} matches for '{text}'."
        elem = elements[nth_result - 1]
        driver.execute_script("arguments[0].scrollIntoView(true);", elem)
        result += f"Focused on element {nth_result} of {len(elements)}"
        return result
