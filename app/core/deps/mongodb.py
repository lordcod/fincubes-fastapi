from fastapi import Request


def get_mongo_collection(name: str):
    def wrapped(request: Request):
        return request.app.state.mongodb_db[name]
    return wrapped
