"""Local stand-ins for the Responses API and the Teams connector. Dev only.

    python dev/fakes.py
    CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=true RESPONSES_BASE_URL=http://127.0.0.1:5001 RESPONSES_API_KEY=x RESPONSES_MODEL=x python -m bridge
    dev/send.sh "Hallo"
"""
import json, asyncio
from aiohttp import web

async def responses(req):
    body = await req.json()
    conv = body.get("conversation") or "thr_new"
    print("RESPONSES <-", json.dumps({k: body.get(k) for k in ("input", "conversation", "stream")}), flush=True)
    resp = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
    await resp.prepare(req)
    async def ev(t, **kw):
        await resp.write(f"event: {t}\ndata: {json.dumps({'type': t, 'sequence_number': 0, **kw})}\n\n".encode())
    base = {"id": "resp_1", "object": "response", "created_at": 0, "model": "m", "output": [], "parallel_tool_calls": True, "tool_choice": "auto", "tools": [], "conversation": {"id": conv}}
    await ev("response.created", response={**base, "status": "in_progress"})
    await ev("response.web_search_call.in_progress", output_index=0, item_id="ws_1")
    for w in ["Hallo ", "aus ", "dem ", "Fake-", "Server."]:
        await asyncio.sleep(0.4)
        await ev("response.output_text.delta", delta=w, item_id="msg_1", output_index=0, content_index=0, logprobs=[])
    await ev("response.completed", response={**base, "status": "completed"})
    await resp.write_eof(); return resp

async def connector(req):
    a = await req.json()
    ents = [e for e in a.get("entities", []) if e.get("type") == "streaminfo"]
    print(f"TEAMS    <- {a['type']:<8} {str(ents[0] if ents else ''):<75} {a.get('text')!r}", flush=True)
    return web.json_response({"id": "act_1"})

app = web.Application()
app.router.add_post("/responses", responses)
app.router.add_post("/v3/conversations/{cid}/activities", connector)
app.router.add_post("/v3/conversations/{cid}/activities/{aid}", connector)
app.router.add_put("/v3/conversations/{cid}/activities/{aid}", connector)
web.run_app(app, host="127.0.0.1", port=5001, print=None)
