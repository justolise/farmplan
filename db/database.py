import atexit
from pymongo import MongoClient
from config.settings import settings


class MongoDatabase:
    def __init__(self):
        # Connect to MongoDB using the URI from settings
        self.client = MongoClient(settings.MONGODB_URI)
        # Use a database named 'farmplan'
        self.db = self.client['farmplan']

    def get_collection(self, name):
        return self.db[name]

    def close(self):
        # No-op on the singleton so individual callers (e.g. market_tool)
        # closing their session reference don't invalidate the shared pool.
        pass

    def shutdown(self):
        try:
            self.client.close()
        except Exception:
            pass

    def __call__(self):
        return self


# Singleton instance for the app
db_instance = MongoDatabase()
atexit.register(db_instance.shutdown)


def SessionLocal():
    """Callable returning the Mongo database instance for backward compatibility."""
    return db_instance


def get_db():
    yield db_instance


def init_db():
    """No-op for MongoDB as collections are created on first insert."""
    pass
