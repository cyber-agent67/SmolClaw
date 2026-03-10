"""Get address information interaction."""

import socket

from helium import get_driver

from agentic_navigator.entities.browser.Address import Address


class GetAddress:
    @staticmethod
    def execute() -> Address:
        """Gets current address information from browser and system."""
        address = Address()

        try:
            driver = get_driver()
            address.current_page_url = driver.current_url
            address.browser_title = driver.title if driver.title else "No Title"
        except Exception:
            address.current_page_url = "Unable to access driver"
            address.browser_title = "No Title"

        try:
            hostname = socket.gethostname()
            address.system_hostname = hostname
            address.local_ip_address = socket.gethostbyname(hostname)
        except Exception:
            address.system_hostname = "unknown"
            address.local_ip_address = "unknown"

        return address
