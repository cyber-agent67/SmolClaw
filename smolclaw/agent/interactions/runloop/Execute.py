"""Execute runloop interaction."""

from smolclaw.agent.entities.runtime.AgentState import AgentState
from smolclaw.agent.entities.runtime.Intent import Intent
from smolclaw.agent.interactions.planner.GeneratePlan import GeneratePlan
from smolclaw.agent.interactions.smolhand.Observe import SmolhandObserve
from smolclaw.config import load_config
from smolhand import OpenAICompatClient, SmolhandRunner, default_tools


HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
HUGGINGFACE_DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


class ExecuteRunloop:
    @staticmethod
    def execute(intent: Intent, max_loops: int = 10) -> AgentState:
        state = AgentState()
        state.goal = intent.user_input
        state.max_loops = max_loops

        plan = GeneratePlan.execute(intent)
        state.current_phase = "planning"
        state.context.extend(plan.steps_description)
        state.context.append(plan.strategy)

        cfg = load_config()
        model = cfg.get("model", HUGGINGFACE_DEFAULT_MODEL)
        base_url = cfg.get("base_url", HUGGINGFACE_BASE_URL)
        api_key = cfg.get("api_key") or cfg.get("hf_token", "")

        try:
            llm = OpenAICompatClient(model=model, base_url=base_url, api_key=api_key)
            runner = SmolhandRunner(llm_client=llm, tools=default_tools())

            state.current_phase = "executing"
            state.final_answer = runner.run(intent.user_input, max_loops=max_loops)
            state.loop_count = 1
            state.current_phase = "done"
            state.done = True
        except Exception as exc:
            state.error = str(exc)
            state.current_phase = "error"

            try:
                observation = SmolhandObserve.execute()
                state.context.append(observation)
                state.final_answer = (
                    f"smolhand execution failed: {exc}\n\n"
                    f"Current page observation:\n{observation}"
                )
            except Exception:
                state.final_answer = f"smolhand execution failed: {exc}"

            state.done = True
        return state
