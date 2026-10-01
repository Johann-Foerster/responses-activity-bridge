import logging
from os import environ

from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    TurnState,
)
from openai import AsyncOpenAI

from .agent import register_handlers
from .settings import ResponsesSettings


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=environ.get("LOG_LEVEL", "INFO"))

    sdk_config = load_configuration_from_env(environ)
    storage = MemoryStorage()
    connections = MsalConnectionManager(**sdk_config)
    adapter = CloudAdapter(connection_manager=connections)
    authorization = Authorization(storage, connections, **sdk_config)
    agent = AgentApplication[TurnState](
        storage=storage, adapter=adapter, authorization=authorization, **sdk_config
    )

    settings = ResponsesSettings.from_env()
    client = AsyncOpenAI(base_url=settings.base_url, api_key=settings.api_key)
    register_handlers(agent, client, settings, environ.get("DEFAULT_LANGUAGE", "de"))

    async def messages(request: Request) -> Response:
        return await start_agent_process(request, agent, adapter)

    bot = Application(middlewares=[jwt_authorization_middleware])
    bot["agent_configuration"] = connections.get_default_connection_configuration()
    bot.router.add_post("/messages", messages)

    web = Application()
    web.router.add_get("/healthz", lambda _: Response(status=200))
    web.add_subapp("/api", bot)

    run_app(web, host=environ.get("HOST", "0.0.0.0"), port=int(environ.get("PORT", 3978)))


if __name__ == "__main__":
    main()
