"""Florence-2 model singleton loaded once and reused."""


class FlorenceModelSingleton:
    _instance = None
    _model = None
    _processor = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model(self):
        return self._model

    @property
    def processor(self):
        return self._processor

    @property
    def device(self):
        return self._device

    def load(self, model_id: str = "microsoft/Florence-2-large", device: str = "cuda", dtype: str = "float16") -> None:
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        torch_dtype = torch.float16 if dtype == "float16" else torch.float32

        self._processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self._model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch_dtype, trust_remote_code=True).to(device)
        self._device = device

    def unload(self) -> None:
        import gc

        import torch

        self._model = None
        self._processor = None
        self._device = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
