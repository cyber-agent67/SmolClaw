"""Extraction-focused browser sub-agent exports."""

from smolclaw.agent.interactions.browser.GetPageSource import GetPageSource
from smolclaw.agent.interactions.dom.GetTree import GetDOMTree
from smolclaw.agent.interactions.perception.DescribeDOM import DescribeDOM

__all__ = ["GetPageSource", "GetDOMTree", "DescribeDOM"]