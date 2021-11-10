from typing import Dict
import aiohttp
import orjson

from labbie import errors


async def load_enchant_stat_ids(session: aiohttp.ClientSession = None) -> Dict[str, str]:
    created_session = False
    if session is None:
        created_session = True
        session = aiohttp.ClientSession()

    try:
        resp = await session.get('https://www.pathofexile.com/api/trade/data/stats')
        content = await resp.text()
        result = orjson.loads(content)['result']
        for stat_type_data in result:
            label = stat_type_data['label']
            if label == 'Enchant':
                return {e['text']: e['id'] for e in stat_type_data['entries']}

        raise errors.UnableToLoadEnchantStatIds
    finally:
        if created_session:
            await session.close()
