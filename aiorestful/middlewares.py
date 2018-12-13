from aiohttp.web import middleware, json_response


@middleware
async def json_middleware(request, handler):
    status = 200
    resp = await handler(request)
    if isinstance(resp, (list, set, tuple)):
        resp, status = resp

    return json_response(resp, status=status)
