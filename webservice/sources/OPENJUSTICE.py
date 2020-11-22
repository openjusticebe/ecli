import json
import re
import webservice.lib_misc as lm
from webservice.lib_async_tools import urlIsPdf
import logging
import requests
from typing import List, NamedTuple
logger = logging.getLogger(__name__)

LEVEL_COUNTRY = 'country'
LEVEL_COURT = 'court'
LEVEL_YEAR = 'year'
LEVEL_DOCUMENT = 'document'


def oj_list_query(config: dict, level: str, data: dict = {}) -> dict:
    server = config['openjustice']['doc_api']
    response = requests.get(
        f"{server}/list",
        params={'level': level, 'data': json.dumps(data)}
    )
    response.raise_for_status()
    print(response.content)
    return response.json()


class OPENJUSTICE:
    country = 'BE'
    data = []

    @staticmethod
    def docMatch(config: dict, num: str) -> bool:
        # Anything terminating with .OJ
        mask = re.compile('^.*\.OJ$')
        return bool(mask.match(num))

    @staticmethod
    def getCodes(config: dict) -> List[str]:
        return oj_list_query(config, LEVEL_COURT, {'country': 'BE'})

    @staticmethod
    def getYears(config: dict, code: str) -> List[str]:
        return [str(y) for y in oj_list_query(config, LEVEL_YEAR, {'country': 'BE', 'court': code})]

    @staticmethod
    def checkYear(config, year: int, code: str) -> List[str]:
        years = oj_list_query(config, LEVEL_YEAR, {'country': 'BE', 'court': code})
        return int(year) in years

    @staticmethod
    def getDocuments(config: dict, code: str, year: int) -> List[str]:
        return oj_list_query(
            config,
            LEVEL_DOCUMENT,
            {'country': 'BE', 'court': code, 'year': year}
        )

    @staticmethod
    async def getUrls(config: dict, eclip: NamedTuple, forceType: bool=False) -> List[dict]:
        # FIXME: add raw text output
        server = config['openjustice']['doc_api']

        urls = [{
            'rel': 'default',
            'href': f"{server}/html/{eclip.raw}"
        }, {
            'rel': 'html',
            'href': f"{server}/html/{eclip.raw}"
        }]

        if not forceType:
            return urls

        return lm.urlGetType(forceType, urls)

    @staticmethod
    def getDocData(config: dict, eclip: NamedTuple) -> dict:
        return {
            'logo': 'https://openjustice.be/wp-content/uploads/2020/10/cropped-Open-Justice.png',
            'website': 'https://openjustice.be/',
            'court': eclip.court,
            'source': 'OPENJUSTICE',
            'year': eclip.year,
            'decision': eclip.num,
        }

    @staticmethod
    def init():
        # FIXME: In the future, maybe cache some results right here
        pass
