import asyncio
import json


def pyodide_post_json_request(url: str, headers: dict[str, str], body: dict, **kwargs):
    if not headers.get("Content-Type"):
        headers["Content-Type"] = "application/json"

    loop = asyncio.get_event_loop()

    return loop.run_until_complete(
        pyodide_fetch(
            url, method="POST", headers=headers, body=json.dumps(body), **kwargs
        )
    )


async def pyodide_fetch(url: str, **kwargs):
    from pyodide.http import pyfetch  # type: ignore

    response = await pyfetch(url, **kwargs)
    return await response.text()
