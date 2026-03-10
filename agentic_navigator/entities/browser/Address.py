"""Address entity - pure state container."""


class Address:
    def __init__(self):
        self.current_page_url: str = ""
        self.system_hostname: str = ""
        self.local_ip_address: str = ""
        self.browser_title: str = ""
