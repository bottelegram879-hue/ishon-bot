"""Two bots behind one public port: /ishonch/... must reach the second process unchanged.

Run from the project folder:  python tests/proxy_test.py
"""
import asyncio
import os
import sys

os.environ.update(PROXY_ROUTES="ishonch=18102", BOT_TOKEN="123456:TEST", DATABASE_URL="sqlite+aiosqlite://")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp  # noqa: E402
from aiohttp import web  # noqa: E402

from bot.webapp import make_app  # noqa: E402

FAILS = []


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


async def echo(request: web.Request) -> web.Response:
    return web.json_response({"path": request.path, "query": request.query_string,
                              "secret": request.headers.get("X-Telegram-Bot-Api-Secret-Token"),
                              "body": (await request.read()).decode()})


async def main():
    second = web.Application()
    second.router.add_route("*", "/{tail:.*}", echo)
    r2 = web.AppRunner(second)
    await r2.setup()
    await web.TCPSite(r2, "127.0.0.1", 18102).start()
    r1 = web.AppRunner(make_app(None))
    await r1.setup()
    await web.TCPSite(r1, "127.0.0.1", 18101).start()
    async with aiohttp.ClientSession() as http:
        async with http.post("http://127.0.0.1:18101/ishonch/tg/webhook", data="upd",
                             headers={"X-Telegram-Bot-Api-Secret-Token": "s3"}) as r:
            j = await r.json()
            check(j["path"] == "/tg/webhook" and j["secret"] == "s3" and j["body"] == "upd",
                  "webhook update forwarded with its secret header")
        async with http.get("http://127.0.0.1:18101/ishonch/?lang=uz") as r:
            j = await r.json()
            check(j["path"] == "/" and j["query"] == "lang=uz", "form page forwarded with the language")
        async with http.get("http://127.0.0.1:18101/ishonch?lang=uz", allow_redirects=False) as r:
            check(r.status == 302 and r.headers["Location"] == "/ishonch/?lang=uz", "/ishonch redirects to /ishonch/")
        async with http.get("http://127.0.0.1:18101/ping") as r:
            check(await r.text() == "ok", "first bot still answers its own routes")
    await r2.cleanup()
    async with aiohttp.ClientSession() as http:
        async with http.get("http://127.0.0.1:18101/ishonch/ping") as r:
            check(r.status == 502, "second bot down -> 502 instead of a crash")
    await r1.cleanup()
    print(f"\nTOTAL: {len(FAILS)} failed", FAILS)


asyncio.run(main())
