from datetime import datetime
from bson import ObjectId


class MongoRecord:
    def __init__(self, data=None, **kwargs):
        data_dict = dict(data or {})
        data_dict.update(kwargs)
        self._data = data_dict
        for k, v in data_dict.items():
            setattr(self, k, v)
        if "_id" in data_dict:
            self.id = str(data_dict["_id"])
        elif "id" not in data_dict:
            self.id = None

    def __getattr__(self, item):
        if item in self._data:
            return self._data[item]
        return None

    def __getitem__(self, item):
        return self._data.get(item)

    def __setitem__(self, item, value):
        self._data[item] = value
        setattr(self, item, value)

    def __contains__(self, item):
        return item in self._data

    def get(self, item, default=None):
        return self._data.get(item, default)

    def to_dict(self):
        return self._data

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._data}>"


class FarmProfile(MongoRecord):
    pass


class Field(MongoRecord):
    pass


class ActivityLog(MongoRecord):
    pass


class MarketReport(MongoRecord):
    pass


# Backward compatibility
Base = object
