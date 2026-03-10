"""Get DOM tree interaction."""

import concurrent.futures
import json

from bs4 import BeautifulSoup
from helium import get_driver

from agentic_navigator.entities.browser.DOMTree import DOMTree


class GetDOMTree:
    @staticmethod
    def execute() -> DOMTree:
        """Retrieves the full DOM tree of the current page."""

        def element_to_dict(element):
            if element.name is None:
                stripped = element.strip()
                if stripped:
                    return {"type": "text", "content": stripped}
                return None

            result = {"tag": element.name, "attrs": element.attrs, "children": []}
            for child in element.children:
                child_dict = element_to_dict(child)
                if child_dict:
                    result["children"].append(child_dict)
            return result

        def parse_html_in_thread(html_content: str) -> str:
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                return json.dumps(element_to_dict(soup))
            except Exception as e:
                return f"Error parsing HTML: {str(e)}"

        driver = get_driver()
        html_content = driver.page_source

        dom_tree = DOMTree()
        dom_tree.raw_html = html_content

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(parse_html_in_thread, html_content)
            try:
                dom_tree.json_string = future.result(timeout=30)
            except Exception as e:
                dom_tree.json_string = f"Error during threaded parsing: {str(e)}"

        return dom_tree
