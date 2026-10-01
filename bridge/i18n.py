from dataclasses import dataclass


@dataclass(frozen=True)
class Messages:
    thinking: str
    new_conversation: str
    error: str
    status: dict[str, str]  # Responses event type -> informative update


MESSAGES: dict[str, Messages] = {
    "de": Messages(
        thinking="Denke nach…",
        new_conversation="Neue Unterhaltung gestartet.",
        error="Entschuldigung, beim Erzeugen der Antwort ist ein Fehler aufgetreten.",
        status={
            "response.reasoning_summary_part.added": "Denke nach…",
            "response.web_search_call.in_progress": "Suche im Web…",
            "response.file_search_call.in_progress": "Durchsuche Dokumente…",
            "response.code_interpreter_call.in_progress": "Führe Code aus…",
            "response.image_generation_call.in_progress": "Erzeuge Bild…",
            "response.mcp_call.in_progress": "Rufe Werkzeug auf…",
            "response.mcp_list_tools.in_progress": "Lade Werkzeuge…",
        },
    ),
    "en": Messages(
        thinking="Thinking…",
        new_conversation="Started a new conversation.",
        error="Sorry, something went wrong while generating the answer.",
        status={
            "response.reasoning_summary_part.added": "Thinking…",
            "response.web_search_call.in_progress": "Searching the web…",
            "response.file_search_call.in_progress": "Searching documents…",
            "response.code_interpreter_call.in_progress": "Running code…",
            "response.image_generation_call.in_progress": "Generating image…",
            "response.mcp_call.in_progress": "Calling tool…",
            "response.mcp_list_tools.in_progress": "Loading tools…",
        },
    ),
}


def messages_for(locale: str | None, default: str = "de") -> Messages:
    language = (locale or "").split("-")[0].lower()
    return MESSAGES.get(language) or MESSAGES[default]
