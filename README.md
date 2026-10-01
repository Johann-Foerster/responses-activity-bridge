# responses-activity-bridge

Exposes an existing OpenAI Responses API endpoint (Azure OpenAI or any compatible `/responses`) as a Microsoft Teams agent via the Activity Protocol, using the Microsoft 365 Agents SDK for Python. Model output is streamed into Teams.

## How it works

- Incoming Teams message → `responses.create(stream=True, conversation=<thread id>)`. The thread id is read from `response.conversation.id` on `response.created` and stored per Teams conversation; the first message of a chat sends no id so the server opens a new thread.
- `response.output_text.delta` → `streaming_response.queue_text_chunk` (SDK paces to Teams' 1 req/s and sends cumulative text).
- Tool/reasoning progress events → informative updates ("Searching the web…").
- `response.completed` → final message with AI label, feedback buttons and URL citations.
- `/new` or `/reset` drops the stored thread id; the next message starts a new server thread.
- UI strings (status updates, errors) follow `activity.locale`; German and English live in `bridge/i18n.py`, fallback is `DEFAULT_LANGUAGE`.

If your server reports the thread id somewhere else, adapt `_thread_id()` in `bridge/responses_stream.py` and the `conversation=` argument next to it.

## Run

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in bot credentials + Responses endpoint
python -m bridge
```

Expose `http://localhost:3978/api/messages` via a dev tunnel and set it as the messaging endpoint of your Azure Bot. Add the Teams channel and sideload a Teams app manifest pointing at the bot id.

## Local test without Teams

`dev/fakes.py` plays both the Responses API (streams a fixed German sentence, returns a thread id) and the Teams connector (prints every activity the bridge sends). Run in three terminals:

```bash
python dev/fakes.py
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=true RESPONSES_BASE_URL=http://127.0.0.1:5001 RESPONSES_API_KEY=x RESPONSES_MODEL=x python -m bridge
dev/send.sh "Hallo"; dev/send.sh "Zweite Frage"; dev/send.sh "/new"
```

The fake's output shows the informative updates, the paced `streaming` chunks, the `final` message, and that the second request reuses the thread id. To test against your real Responses server, point `RESPONSES_BASE_URL` at it and keep the fake only as connector.

For a chat UI without Teams, use the [Agents Playground](https://microsoft.github.io/teams-sdk/developer-tools/agents-playground/) with `-c msteams` and the same anonymous setting.

## Limits worth knowing

- Teams streams only in 1:1 chats; in group chats/channels the SDK falls back to a single final message automatically.
- Teams allows ~2 minutes per stream. The SDK ends the stream with a notice if exceeded; the final text is still sent as a normal message.
- The inbound HTTP request is held open for the duration of the turn. Teams may redeliver an activity after ~15 s; dedupe by `activity.id` if you see duplicate answers on slow models.
- `MemoryStorage` is per process. Swap in `microsoft-agents-storage-cosmos` or `-blob` before scaling out.
