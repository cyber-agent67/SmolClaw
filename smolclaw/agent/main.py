"""SMOL claw - EIM architecture main orchestration entrypoint."""

from dotenv import load_dotenv

from smolclaw.agent.config.BrowserConfig import BrowserConfig
from smolclaw.agent.entities.browser.Browser import Browser
from smolclaw.agent.entities.memory.ExperienceMemory import ExperienceMemory
from smolclaw.agent.entities.browser.NavigationStack import NavigationStack
from smolclaw.agent.interactions.agent.Cleanup import CleanupAgent
from smolclaw.agent.interactions.agent.Initialize import InitializeAgent
from smolclaw.agent.interactions.agent.Run import RunAgent
from smolclaw.agent.interactions.browser.Initialize import InitializeBrowser
from smolclaw.agent.interactions.memory.LoadExperiences import LoadExperiences
from smolclaw.agent.interactions.screenshot.Capture import CaptureScreenshot


def run_agent_with_args(args):
    """Main orchestration function called by navigate.py with parsed args."""
    load_dotenv()

    prompt = args.prompt or "Perform a web search and navigate to find relevant information"

    experience_memory = ExperienceMemory()
    LoadExperiences.execute(experience_memory)

    navigation_stack = NavigationStack()
    navigation_stack.stack = [args.url]

    config = BrowserConfig()
    browser = InitializeBrowser.execute(config)

    def screenshot_callback(memory_step, agent):
        CaptureScreenshot.execute(memory_step, agent)

    agent = InitializeAgent.execute(
        model_type=args.model_type,
        model_id=args.model_id,
        screenshot_callback=screenshot_callback,
    )

    try:
        return RunAgent.execute(
            agent=agent,
            prompt=prompt,
            start_url=args.url,
            experience_memory=experience_memory,
            navigation_stack=navigation_stack,
        )
    finally:
        CleanupAgent.execute(browser)


def cleanup_resources():
    """Legacy cleanup function for backward compatibility."""
    browser = Browser()
    browser.is_running = True
    CleanupAgent.execute(browser)
