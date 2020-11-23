import json
import re
from webservice.lib_async_tools import urlIsPdf
import logging
from typing import List, NamedTuple
import webservice.lib_misc as lm
logger = logging.getLogger(__name__)


class GHCC:
    country = 'BE'
    code = 'GHCC'
    data = []

    @staticmethod
    def docMatch(config, num):
        mask = re.compile('^\d{4}\.\d{1,4}(f|n|d)?$')
        return bool(mask.match(num))

    @staticmethod
    def getYears(config, _code):
        return GHCC.data.keys()

    @staticmethod
    async def getUrls(config, eclip, forceType=None):
        name = eclip.num.split('.')
        arr_num = name[1]
        urls = [{
            'rel': 'default',
            'href': f"https://www.const-court.be/public/f/{eclip.year}/{eclip.year}-{arr_num}.pdf"
        }, {
            'rel': 'pdf',
            'href': f"https://www.const-court.be/public/f/{eclip.year}/{eclip.year}-{arr_num}.pdf"
        }]
        if not forceType:
            return urls

        return lm.urlGetType(forceType, urls)

    @staticmethod
    def getCodes(config):
        return [GHCC.code]

    @staticmethod
    def checkYear(_config, year, _code):
        return year in GHCC.data.keys()

    @staticmethod
    def getDocuments(config: dict, code: str, year: int) -> List[str]:
        collection = []
        for record in GHCC.data[str(year)]:
            name = '{year}.{num}{lang}'.format(
                year=record['year'],
                num=record['num'],
                lang='f' if record['language'] == 'french' else 'n'
            )
            collection.append(name)

        return collection

    @staticmethod
    def getDocData(config, eclip):
        return {
            'logo': 'https://www.const-court.be/images/titre_index3.gif',
            'website': 'https://www.const-court.be/',
            'court': GHCC.code,
            'source': 'GHCC',
            'year': eclip.year,
            'decision': eclip.num,
        }

    @staticmethod
    def init():
        """
        FIXME: This is purely experimental. Prepare some persistant storage for this.
        {"num": 208168, "year": 2010, "language": "french", "type": "arr"}
        {"num": 72214, "year": 1998, "language": "dutch", "type": "arr"}
        """
        data = {}
        with open('./resources/GHCC_def.json', 'r') as f:
            for line in f:
                rec = json.loads(line)
                index = str(rec['year'])
                if index in data:
                    data[index].append(rec)
                else:
                    data[index] = [rec]
        GHCC.data = data
