import json

from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import codes


class RequestSearch(BaseModel):
    key: str
    cx: str


class RequestAIParams(BaseModel):
    provider: str
    model: str
    key: str


class RequestAI(BaseModel):
    base: RequestAIParams
    thinking: RequestAIParams


class Request(BaseModel):
    q: str
    ai: RequestAI
    search: RequestSearch


class Response(BaseModel):
    code: int = codes.success
    msg: str = ''
    data: dict = None


def response(code: int = codes.success, msg: str = '', data: dict = None):
    return 'data: ' + json.dumps({
        'code': code,
        'msg': msg,
        'data': data
    }) + '\n\n'


def streaming_response(code: int = codes.success, msg: str = '', data: dict = None):
    return StreamingResponse(response(code=code, msg=msg, data=data), media_type="text/event-stream")


class IntentAnalysis(BaseModel):
    type: int = 0
    thinking: bool = False
    kw: str = ''
