from aiohttp.web import route

from .base import Resource
from .middlewares import json_middleware


__all__ = [
    'Resource',
    'setup'
]


def setup_routes(app, resources, api_prefix):
    resources = resources or []
    for resource in resources:
        res = resource()
        prefix = res.get_url_prefix(api_prefix=api_prefix)
        prefix_id = '{}/{{id}}'.format(prefix)

        routes = []
        if 'list' in res.get_methods_allowed():
            routes.append(route('GET', prefix, res.handle_list))

        if 'get' in res.get_methods_allowed():
            routes.append(route('GET', prefix_id, res.handle_get))

        if 'create' in res.get_methods_allowed():
            routes.append(route('POST', prefix, res.handle_create))

        if 'delete' in res.get_methods_allowed():
            routes.append(route('DELETE', prefix_id, res.handle_delete))

        if 'update' in res.get_methods_allowed():
            routes.append(route('PUT', prefix_id, res.handle_update))

        app.add_routes(routes)
        app.add_routes([
            route(method, '{}{}'.format(prefix, path), getattr(res, fnx))
            for (method, path, fnx) in res.get_extra()
        ])

    return app


def setup_middleware(app):
    app.middlewares.append(json_middleware)


def setup(app, resources=None, api_prefix='api'):
    app = setup_routes(app, resources, api_prefix)
    app = setup_middleware(app)
    return app
