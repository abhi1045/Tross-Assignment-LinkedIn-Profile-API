"""Ad-hoc Voyager connectivity check.

Prints status codes only. Never prints cookie
values. Delete after debugging.
"""

import asyncio

import httpx

from app.config import settings
from app.services.linkedin_voyager import (
    VOYAGER_API,
    VOYAGER_ORIGIN,
    _quote_jsessionid,
    _csrf_from_jsessionid,
)

VANITY = "danielolegarioferdinandovaz"


async def main() -> None:

    print(
        "li_at configured:",
        bool(settings.linkedin_li_at),
        "len:",
        len(settings.linkedin_li_at or ""),
    )
    print(
        "JSESSIONID configured:",
        bool(settings.linkedin_jsessionid),
    )

    cookies = {"li_at": settings.linkedin_li_at or ""}

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20.0),
        follow_redirects=True,
        headers={
            "User-Agent": settings.linkedin_user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        },
    ) as client:

        jsessionid = settings.linkedin_jsessionid

        if not jsessionid:
            for url in (
                f"{VOYAGER_API}/me",
                f"{VOYAGER_ORIGIN}/",
            ):
                r = await client.get(
                    url,
                    cookies=cookies,
                    headers={"Accept": "application/json"},
                )
                got = r.cookies.get("JSESSIONID")
                print(
                    f"bootstrap {url} -> {r.status_code}, "
                    f"JSESSIONID received: {bool(got)}"
                )
                if got:
                    jsessionid = got
                    break

        if not jsessionid:
            print("NO JSESSIONID -> session unusable")
            return

        cookies["JSESSIONID"] = _quote_jsessionid(
            jsessionid
        )

        headers = {
            "Accept": "application/json",
            "csrf-token": _csrf_from_jsessionid(
                jsessionid
            ),
            "x-restli-protocol-version": "2.0.0",
            "x-li-lang": "en_US",
            "Referer": f"{VOYAGER_ORIGIN}/in/{VANITY}/",
        }

        me = await client.get(
            f"{VOYAGER_API}/me",
            cookies=cookies,
            headers=headers,
        )
        print("voyager /me ->", me.status_code)
        if me.status_code != 200:
            print("body head:", me.text[:300])

        url = (
            f"{VOYAGER_API}/identity/profiles/"
            f"{VANITY}/profileView"
        )
        r = await client.get(
            url,
            cookies=cookies,
            headers=headers,
        )
        print("profileView ->", r.status_code)
        print(
            "content-type:",
            r.headers.get("content-type"),
        )
        if r.status_code != 200:
            print("body head:", r.text[:500])
        else:
            data = r.json()
            print("top-level keys:", list(data)[:15])


asyncio.run(main())
