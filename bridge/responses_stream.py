"""Maps a Responses API SSE stream onto the three things a chat channel can render:
status updates, text deltas and a completion with citations."""

from dataclasses import dataclass, field
from typing import AsyncIterator

from microsoft_agents.hosting.aiohttp import Citation
from openai import AsyncOpenAI
from openai.types.responses import Response

from .settings import ResponsesSettings


@dataclass(frozen=True)
class Status:
    event_type: str  # translated by the caller, see i18n.Messages.status


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ThreadStarted:
    thread_id: str


@dataclass(frozen=True)
class Completed:
    citations: list[Citation] = field(default_factory=list)


Event = Status | TextDelta | ThreadStarted | Completed


class ResponsesError(Exception):
    pass


STATUS_EVENTS = frozenset(
    {
        "response.reasoning_summary_part.added",
        "response.web_search_call.in_progress",
        "response.file_search_call.in_progress",
        "response.code_interpreter_call.in_progress",
        "response.image_generation_call.in_progress",
        "response.mcp_call.in_progress",
        "response.mcp_list_tools.in_progress",
    }
)


async def stream_response(
    client: AsyncOpenAI,
    settings: ResponsesSettings,
    user_text: str,
    thread_id: str | None,
) -> AsyncIterator[Event]:
    """`thread_id` is the server-side conversation; None lets the server open a new one."""
    stream = await client.responses.create(
        model=settings.model,
        instructions=settings.instructions,
        input=user_text,
        conversation=thread_id,
        stream=True,
    )
    async for event in stream:
        match event.type:
            case "response.created":
                if (started := _thread_id(event.response)) and started != thread_id:
                    yield ThreadStarted(started)
            case "response.output_text.delta":
                yield TextDelta(event.delta)
            case "response.completed" | "response.incomplete":
                yield Completed(_citations(event.response))
            case "response.failed":
                error = event.response.error
                raise ResponsesError(error.message if error else "response failed")
            case "error":
                raise ResponsesError(event.message)
            case kind if kind in STATUS_EVENTS:
                yield Status(kind)


def _thread_id(response: Response) -> str | None:
    return response.conversation.id if response.conversation else None


def _citations(response: Response) -> list[Citation]:
    seen: dict[str, Citation] = {}
    for item in response.output:
        if item.type != "message":
            continue
        for part in item.content:
            if part.type != "output_text":
                continue
            for annotation in part.annotations:
                if annotation.type == "url_citation" and annotation.url not in seen:
                    seen[annotation.url] = Citation(
                        title=annotation.title, url=annotation.url, content=annotation.title
                    )
    return list(seen.values())
