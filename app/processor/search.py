import requests

from app.config import config
from app.model import model


def search_google(data: model.Request, kw: str):
    url = f'{config.search['cse']['url']}?key={data.search.key}&cx={data.search.cx}&q={kw if kw is not None and len(kw) > 0 else data.q}'

    try:
        res = requests.get(url=url)
        if not res.ok:
            return None

        return res.json()
    except Exception as e:
        print(e)
        return None
