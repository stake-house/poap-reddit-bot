from databases import Database
from ormar import Model


class EventDataStore:

    def __init__(self, db: Database):
        self.db = db

    async def get(self, cls: Model, *args, **kwargs):
        return await cls.objects.get_or_none(*args, **kwargs)

    async def get_filter(self, cls: Model, *args, **kwargs):
        return await cls.objects.filter(*args, **kwargs).get_or_none()

    async def get_filter_first(self, cls: Model, *args, **kwargs):
        return await cls.objects.filter(*args, **kwargs).first()

    async def get_or_create(self, cls: Model, *args, **kwargs):
        return await cls.objects.get_or_create(*args, **kwargs)

    async def create(self, cls: Model, *args, **kwargs):
        obj = cls(*args, **kwargs)
        await obj.save()
        return obj