import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "TownLink - Multi-Agent Interoperability Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    # gemini | openrouter. Used only when both API keys have a value. Empty means gemini.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL") or "gemini-2.5-flash"
    GEMINI_REASONING_MODEL: str = os.getenv("GEMINI_REASONING_MODEL") or "gemini-2.5-flash"
    OPENROUTER_VISION_MODEL: str = os.getenv("OPENROUTER_VISION_MODEL") or "nvidia/nemotron-3.5-super-vl:free"
    OPENROUTER_REASONING_MODEL: str = os.getenv("OPENROUTER_REASONING_MODEL") or "nvidia/nemotron-3.5-super-vl:free"
    OPENROUTER_API_BASE: str = os.getenv("OPENROUTER_API_BASE") or "https://openrouter.ai/api/v1"

    ATHENS_GIS_ARCGIS_URL: str = "https://gis.cityofathens.gr/arcgis/rest/services"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    NOMINATIM_API_URL: str = "https://nominatim.openstreetmap.org/reverse"
    OASA_TELEMATICS_BASE_URL: str = "http://telematics.oasa.gr/api/"
    MITOS_API_BASE_URL: str = "https://api.mitos.gov.gr/v1"
    INTERNAL_WEBHOOK_BASE_URL: str = os.getenv("INTERNAL_WEBHOOK_BASE_URL", "http://127.0.0.1:8000/api/webhooks")
    HTTP_TIMEOUT: float = 12.0

    ATTICA_REGION_MAJOR_AVENUES: list[str] = [
        "συγγρου", "syngrou", "syggrou", "αλεξανδρας", "alexandras", "κηφισιας", "kifisias",
        "μεσογειων", "mesogeion", "πατησιων", "patision", "28ης οκτωβριου", "κατεχακη", "katechaki",
        "βασιλισσης σοφιας", "vasilissis sofias", "βασιλεως κωνσταντινου", "vasileos konstantinou",
        "βασιλισσης αμαλιας", "vasilissis amalias", "ηλιουπολεως", "ilioupoleos", "βουλιαγμενης", "vouliagmenis",
        "πειραιως", "peiraios", "ιερα οδος", "iera odos", "καλλιρροης", "kallirrois", "αθηνων", "athinon"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def active_llm_provider() -> str | None:
    """Provider used for both vision and reasoning.

    The provider is whichever API key has a value. When both keys are set,
    LLM_PROVIDER chooses; an empty LLM_PROVIDER keeps Gemini.
    """
    has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    has_openrouter = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip())
    if has_gemini and has_openrouter:
        choice = (settings.LLM_PROVIDER or "").strip().lower()
        return "openrouter" if choice == "openrouter" else "gemini"
    if has_openrouter:
        return "openrouter"
    if has_gemini:
        return "gemini"
    return None


def vision_model_name() -> str:
    if active_llm_provider() == "openrouter":
        return settings.OPENROUTER_VISION_MODEL
    return settings.GEMINI_VISION_MODEL


def reasoning_model_name() -> str:
    if active_llm_provider() == "openrouter":
        return settings.OPENROUTER_REASONING_MODEL
    return settings.GEMINI_REASONING_MODEL


def active_llm_api_key() -> str:
    if active_llm_provider() == "openrouter":
        return settings.OPENROUTER_API_KEY
    return settings.GEMINI_API_KEY


def bind_request_llm_keys(
    gemini_key: str | None = None,
    openrouter_key: str | None = None,
    session_key: str | None = None,
) -> str:
    """Apply optional request keys, then return the provider that has a value.

    A generic session key replaces the provider already selected from the environment.
    Named headers set that provider's key directly.
    """
    if gemini_key and gemini_key.strip():
        settings.GEMINI_API_KEY = gemini_key.strip()
    if openrouter_key and openrouter_key.strip():
        settings.OPENROUTER_API_KEY = openrouter_key.strip()
    named = bool((gemini_key or "").strip() or (openrouter_key or "").strip())
    session = (session_key or "").strip()
    if session and not named:
        if active_llm_provider() == "openrouter":
            settings.OPENROUTER_API_KEY = session
        else:
            settings.GEMINI_API_KEY = session
    provider = active_llm_provider()
    if not provider:
        raise ValueError("missing llm api key")
    return provider
