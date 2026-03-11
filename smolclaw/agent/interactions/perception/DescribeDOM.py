"""Describe DOM interaction."""

from bs4 import BeautifulSoup

from smolclaw.agent.entities.perception.DOMDescription import DOMDescription


class DescribeDOM:
    @staticmethod
    def execute(dom_html: str, page_url: str = "") -> DOMDescription:
        desc = DOMDescription()
        desc.page_url = page_url
        soup = BeautifulSoup(dom_html or "", "html.parser")

        if soup.title and soup.title.string:
            desc.page_title = soup.title.string.strip()

        desc.headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]
        desc.paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")[:20] if p.get_text(strip=True)]
        desc.links = [{"text": a.get_text(strip=True), "href": a.get("href", "")} for a in soup.find_all("a")[:50]]
        desc.buttons = [{"text": b.get_text(strip=True), "type": b.get("type", "")} for b in soup.find_all("button")[:50]]
        return desc
