import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import app.processor.ai, app.processor.search
from app.config import codes, config
from app.model import model

# uvicorn app.main:app --host 0.0.0.0 --port 4000
fast_app = FastAPI()

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


async def async_yield(action: str, data: dict = None):
    yield model.response(data={'action': action, 'data': data})
    await asyncio.sleep(0)


async def process_search(data: model.Request, intent: model.IntentAnalysis):
    search_result = app.processor.search.search_google(data, intent.kw)

    if search_result is None:
        yield model.response(data={'action': 'search_error'}), False
    else:
        yield model.response(data={'action': 'search_result', 'data': search_result})

    await asyncio.sleep(0)


async def process_ai(data: model.Request, intent: model.IntentAnalysis):
    stream = app.processor.ai.answer(data, intent.thinking)
    if stream is None:
        yield model.response(data={'action': 'ai_error'}), False
        await asyncio.sleep(0)
        return

    # 分离思考内容和回答内容
    thinking_finished = False

    for chunk in stream:
        content = chunk.choices[0].delta.content

        if intent.thinking:
            if data.ai.thinking.provider == 'silicon':
                reasoning_content = chunk.choices[0].delta.reasoning_content

                if (reasoning_content is None or len(reasoning_content) == 0) and (
                        content is None or len(content) == 0):
                    continue

                yield model.response(data={'action': 'ai_result', 'data': {
                    'reasoning': reasoning_content,
                    'content': content
                }})
            elif data.ai.thinking.provider == 'groq':
                if content is None or len(content) == 0:  # or content == '\n\n'
                    continue

                if thinking_finished == False and content == '\n<think>\n':
                    continue

                if thinking_finished == False and content == '</think>':
                    thinking_finished = True
                    continue

                if not thinking_finished:
                    yield model.response(data={'action': 'ai_result', 'data': {
                        'reasoning': content,
                        'content': ''
                    }})
                else:
                    yield model.response(data={'action': 'ai_result', 'data': {
                        'reasoning': '',
                        'content': content
                    }})
            else:
                if content is None or len(content) == 0:
                    continue

                yield model.response(data={'action': 'ai_result', 'data': {
                    'reasoning': '',
                    'content': content
                }})
        else:
            if content is None or len(content) == 0:
                continue

            yield model.response(data={'action': 'ai_result', 'data': {
                'content': content
            }})

        await asyncio.sleep(0)


async def process(data: model.Request):
    # 意图分析
    yield model.response(data={'action': 'intent_analysis'})
    await asyncio.sleep(0)

    intent = app.processor.ai.intent_analysis(data)
    yield model.response(data={'action': 'intent_analysis_result', 'data': intent.model_dump()})
    await asyncio.sleep(0)

    if intent.type == 1:
        # 仅使用大模型回答
        yield model.response(data={'action': 'ai'})
        await asyncio.sleep(0)

        async for response in process_ai(data, intent):
            if isinstance(response, tuple):
                yield response[0]
            else:
                yield response
    elif intent.type == 2:
        # 搜索 + 大模型回答
        yield model.response(data={'action': 'search'})
        await asyncio.sleep(0)

        # 搜索
        async for response in process_search(data, intent):
            yield model.response(data={'action': 'ai'})
            await asyncio.sleep(0)

            if isinstance(response, tuple):
                yield response[0]
            else:
                yield response

        # 大模型
        async for response in process_ai(data, intent):
            if isinstance(response, tuple):
                yield response[0]
            else:
                yield response
    else:
        # 仅常规搜索
        yield model.response(data={'action': 'search'})
        await asyncio.sleep(0)

        async for response in process_search(data, intent):
            if isinstance(response, tuple):
                yield response[0]
            else:
                yield response


@fast_app.post("/search")
async def search(request: model.Request):
    if len(str.strip(request.q)) <= 0:
        return model.streaming_response(code=codes.param_error)

    return StreamingResponse(process(request), media_type="text/event-stream")


@fast_app.post("/config")
def get_config():
    return model.Response(data=config.ai)
