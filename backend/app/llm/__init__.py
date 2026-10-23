from ..config import Settings
from .base import LabGenerator, TutorModel


def build_models(settings: Settings) -> tuple[LabGenerator, TutorModel]:
    if settings.mode == "gemini":
        from .gemini import GeminiLabGenerator, GeminiTutor, make_client

        if not settings.gemini_api_key:
            raise RuntimeError("FOURWEEKS_MODE=gemini needs GEMINI_API_KEY in the server environment")
        client = make_client(settings.gemini_api_key)
        return GeminiLabGenerator(client, settings.gemini_model), GeminiTutor(client, settings.gemini_model)

    from .deterministic import DeterministicTutor, TemplateLabGenerator

    return TemplateLabGenerator(), DeterministicTutor()
