import json

from openai import OpenAI

from app.config import config
from app.model import model


def intent_analysis(data: model.Request):
    url = config.ai[data.ai.base.provider]['url']
    key = data.ai.base.key

    client_openai = OpenAI(base_url=url, api_key=key)

    try:
        completion = client_openai.chat.completions.create(
            model=data.ai.base.model,
            messages=[{
                "role": "system",
                "content": config.intent_analysis_prompt
            }, {
                "role": "user",
                "content": data.q
            }],
            stream=False,
            response_format={"type": "json_object"},
        )

        res = json.loads(completion.choices[0].message.content)
        result = model.IntentAnalysis(type=res['type'], thinking=res['thinking'], kw=res['kw'])
    except Exception as e:
        result = model.IntentAnalysis()

    return result


def answer(data: model.Request, thinking: bool):
    if thinking:
        url = config.ai[data.ai.thinking.provider]['url']
        key = data.ai.thinking.key
    else:
        url = config.ai[data.ai.base.provider]['url']
        key = data.ai.base.key

    client_openai = OpenAI(base_url=url, api_key=key)

    try:
        stream = client_openai.chat.completions.create(
            model=data.ai.thinking.model if thinking else data.ai.base.model,
            messages=[{
                "role": "user",
                "content": data.q
            }],
            stream=True
        )

        return stream
    except Exception as e:
        return None
