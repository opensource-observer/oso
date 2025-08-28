import asyncio
import json


def get_current_async_loop():
    return asyncio.get_event_loop()


def pyodide_post_json_request(url: str, headers: dict[str, str], body: dict, **kwargs):
    if not headers.get("Content-Type"):
        headers["Content-Type"] = "application/json"

    loop = get_current_async_loop()

    return loop.run_until_complete(
        pyodide_fetch(
            url, method="POST", headers=headers, body=json.dumps(body), **kwargs
        )
    )


async def pyodide_fetch(url: str, **kwargs):
    from pyodide.http import pyfetch

    response = await pyfetch(url, **kwargs)
    return await response.text()
