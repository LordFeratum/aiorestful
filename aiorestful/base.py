class BaseResource:
    name = None
    resource = None
    schema = None
    list_schema = None
    extra = []
    methods_allowed = ['list', 'get', 'update', 'delete']

    def get_extra(self):
        return self.extra

    def get_resource(self):
        return self.resource

    def get_resource_table(self):
        return self.get_resource().__table__

    def get_resource_primary_key(self):
        tbl = self.get_resource_table()
        return tbl.primary_key.columns.values()[0].name

    def get_resource_name(self):
        return self.name or self.get_resource_table().name

    def get_url_prefix(self, api_prefix=None):
        resource_name = self.get_resource_name()
        p = '/{}'.format(resource_name)
        if api_prefix is not None:
            p = '/{}{}'.format(api_prefix, p)

        return p

    def get_schema(self):
        return self.schema

    def get_schema_list(self):
        return self.schema_list or self.get_schema()

    def load_data(self, data, partial=False, schema=None):
        schema = schema or self.get_schema()
        return schema().load(data, partial=partial)

    def dump_data(self, data, many=False, schema=None):
        schema = schema or self.get_schema()
        return schema(many=many).dump(data)

    def get_methods_allowed(self):
        return self.methods_allowed

    def is_method_allowed(self, method):
        return method in self.get_methods_allowed()

    def get_element_id(self):
        element_id = self.request.match_info['id']
        if element_id.isdigit():
            return int(element_id)

        return element_id

    def format_response(self, response):
        return response

    async def retrieve_data(self, partial=False):
        data = await self.request.json()
        return self.load_data(data, partial=partial).data

    async def handle_list(self, request):
        self.request = request
        schema = self.get_schema_list()
        response = self.dump_data(await self.list(), many=True, schema=schema)
        return self.format_response(response.data)

    async def handle_get(self, request):
        self.request = request
        element_id = self.get_element_id()
        response = self.dump_data(await self.get(element_id))
        return self.format_response(response.data)

    async def handle_create(self, request):
        self.request = request
        data = await self.retrieve_data()
        response = self.dump_data(await self.create(data))
        return self.format_response(response.data), 201

    async def handle_delete(self, request):
        self.request = request
        element_id = self.get_element_id()
        response = self.dump_data(await self.delete(element_id))
        return self.format_response(response.data)

    async def handle_update(self, request):
        self.request = request
        element_id = self.get_element_id()
        data = await self.retrieve_data(partial=True)
        response = self.dump_data(await self.update(element_id, data))
        return self.format_response(response.data)

    async def list(self):
        raise NotImplementedError

    async def get(self, element_id):
        raise NotImplementedError

    async def create(self, data):
        raise NotImplementedError

    async def delete(self, element_id):
        raise NotImplementedError

    async def update(self, element_id, data):
        raise NotImplementedError


class Pagination:
    pagination_by = 20

    def get_pagination_by(self):
        return self.request.query.get('per_page', self.pagination_by)

    def get_page(self):
        return int(self.request.query.get('page', '1')) - 1

    def paginate(self, query):
        paginate_by = self.get_pagination_by()
        page = self.get_page()
        offset = page * paginate_by
        return query.limit(paginate_by).offset(offset)


class Resource(BaseResource, Pagination):
    session_attr = 'db'

    def get_session_attr(self):
        return self.session_attr

    async def list(self):
        session_attr = self.get_session_attr()
        tbl = self.get_resource_table()
        async with self.request.app[session_attr].acquire() as conn:
            query = self.paginate(tbl.select())
            objects = []
            async for obj in conn.execute(query):
                objects.append(obj)

            return objects

    async def get(self, element_id):
        session_attr = self.get_session_attr()
        tbl = self.get_resource_table()
        pk = getattr(tbl.c, self.get_resource_primary_key())
        async with self.request.app[session_attr].acquire() as conn:
            query = tbl.select().where(pk == element_id)
            res = await conn.execute(query)
            obj = await res.fetchone()
            return obj

    async def create(self, data):
        session_attr = self.get_session_attr()
        tbl = self.get_resource_table()
        pk = self.get_resource_primary_key()
        pk_column = getattr(tbl.c, pk)
        async with self.request.app[session_attr].acquire() as conn:
            query = tbl.insert().values(**data)
            element_id = await conn.scalar(query)
            query = tbl.select().where(pk_column == element_id)
            res = await conn.execute(query)
            return await res.fetchone()

    async def delete(self, element_id):
        session_attr = self.get_session_attr()
        tbl = self.get_resource_table()
        pk = getattr(tbl.c, self.get_resource_primary_key())
        async with self.request.app[session_attr].acquire() as conn:
            query = tbl.select().where(pk == element_id)
            res = await conn.execute(query)
            obj = await res.fetchone()
            query = tbl.delete().where(pk == element_id)
            await conn.execute(query)

        return obj

    async def update(self, element_id, data):
        session_attr = self.get_session_attr()
        tbl = self.get_resource_table()
        pk = getattr(tbl.c, self.get_resource_primary_key())
        async with self.request.app[session_attr].acquire() as conn:
            query = tbl.update().values(**data).where(pk == element_id)
            await conn.execute(query)
            query = tbl.select().where(pk == element_id)
            res = await conn.execute(query)
            return await res.fetchone()
