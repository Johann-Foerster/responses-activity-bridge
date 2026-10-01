import logging
import re

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState
from openai import AsyncOpenAI

from .i18n import messages_for
from .responses_stream import Completed, Status, TextDelta, ThreadStarted, stream_response
from .settings import ResponsesSettings

logger = logging.getLogger(__name__)

THREAD_ID = "thread_id"


def register_handlers(
    app: AgentApplication[TurnState],
    client: AsyncOpenAI,
    settings: ResponsesSettings,
    default_language: str = "de",
) -> None:
    @app.message(re.compile(r"\s*/(new|reset)\s*"))
    async def on_reset(context: TurnContext, state: TurnState) -> None:
        state.conversation.set_value(THREAD_ID, None)
        msgs = messages_for(context.activity.locale, default_language)
        await context.send_activity(msgs.new_conversation)

    @app.activity("message")
    async def on_message(context: TurnContext, state: TurnState) -> None:
        text = (context.activity.text or "").strip()
        if not text:
            return

        msgs = messages_for(context.activity.locale, default_language)
        stream = context.streaming_response
        stream.set_generated_by_ai_label(True)
        stream.set_feedback_loop(True)
        stream.queue_informative_update(msgs.thinking)

        thread_id = state.conversation.get_value(THREAD_ID)
        try:
            async for event in stream_response(client, settings, text, thread_id):
                match event:
                    case ThreadStarted(thread_id=started):
                        state.conversation.set_value(THREAD_ID, started)
                    case Status(event_type=kind) if kind in msgs.status:
                        stream.queue_informative_update(msgs.status[kind])
                    case TextDelta(text=delta):
                        stream.queue_text_chunk(delta)
                    case Completed(citations=citations):
                        if citations:
                            stream.set_citations(citations)
        except Exception:
            logger.exception("responses stream failed")
            stream.queue_text_chunk(msgs.error)
        finally:
            await stream.end_stream()
