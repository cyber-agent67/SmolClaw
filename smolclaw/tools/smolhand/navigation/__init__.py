"""Navigation-focused browser sub-agent exports."""

from smolclaw.agent.interactions.navigation.ClosePopups import ClosePopups
from smolclaw.agent.interactions.navigation.GoBack import GoBack
from smolclaw.agent.interactions.navigation.GoToURL import GoToURL
from smolclaw.agent.interactions.navigation.SearchOnPage import SearchOnPage
from smolclaw.agent.interactions.scout.FindPathToTarget import FindPathToTarget

__all__ = ["GoToURL", "GoBack", "SearchOnPage", "ClosePopups", "FindPathToTarget"]