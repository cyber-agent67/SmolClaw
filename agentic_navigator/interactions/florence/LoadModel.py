"""Load Florence model interaction."""

from agentic_navigator.models.FlorenceModelSingleton import FlorenceModelSingleton


class LoadFlorenceModel:
    @staticmethod
    def execute(model_id: str = "microsoft/Florence-2-large", device: str = "cuda", dtype: str = "float16"):
        singleton = FlorenceModelSingleton()
        singleton.load(model_id=model_id, device=device, dtype=dtype)
        return singleton
