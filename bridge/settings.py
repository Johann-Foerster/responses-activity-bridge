from dataclasses import dataclass
from os import environ


@dataclass(frozen=True)
class ResponsesSettings:
    base_url: str
    api_key: str
    model: str
    instructions: str | None = None

    @classmethod
    def from_env(cls) -> "ResponsesSettings":
        return cls(
            base_url=environ["RESPONSES_BASE_URL"],
            api_key=environ["RESPONSES_API_KEY"],
            model=environ["RESPONSES_MODEL"],
            instructions=environ.get("RESPONSES_INSTRUCTIONS") or None,
        )
