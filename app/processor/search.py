import json

import requests
import re

from app.config import config
from app.model import model


def search_google(data: model.Request, kw: str):
    cse_url = config.search['cse']['url']
    query = kw if kw is not None and len(kw) > 0 else data.q
    url = f'{cse_url}?key={data.search.key}&cx={data.search.cx}&q={query}'

    try:
        res = requests.get(url=url)
        if not res.ok:
            return None

        return res.json()
    except Exception as e:
        return None


def search_google_js(data: model.Request, kw: str):
    cse_js_url = config.search['cseJS']['url']
    query = kw if kw is not None and len(kw) > 0 else data.q
    cse_cx = config.search['cseJS']['cx']

    try:
        res = requests.get(url=cse_js_url, params={
            'cx': cse_cx,
            'q': query,
            'cse_tok': config.search['cseJS']['cseTok'],
            'rurl': f'https://cse.google.com/cse?cx={cse_cx}',
            'rsz': 'filtered_cse',
            'start': 0,
            'num': 10,
            'hl': 'zh-CN',
            'lr': 'zh-Hans',
            # 'cr': 'countryCN',  # 区域受限的搜索结果: 仅显示所选区域中的搜索结果
            'gl': 'cn',  # 区域
            'source': 'gcsc',
            'cselibv': '75c56d121cde450a',
            'safe': 'off',
            'filter': 0,
            'sort': '',
            'as_oq': '',
            'as_sitesearch': '',
            'callback': 'google.search.cse.api.callback'
        })

        if not res.ok:
            return None

        match = re.search(r'google\.search\.cse\.api\.callback\((.*?)\);', res.text, re.DOTALL)

        if match:
            results = json.loads(match.group(1))['results']
            if results is None:
                return None

            items = []
            for result in results:
                items.append({
                    'displayLink': result['visibleUrl'],
                    'htmlFormattedUrl': result['formattedUrl'],
                    'link': result['url'],
                    'htmlTitle': result['title'],
                    'htmlSnippet': result['content']
                })

            return {
                'items': items
            }
        else:
            return None
    except Exception as e:
        return None
