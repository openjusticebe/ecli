import json
import re
import webservice.lib_misc as lm
from webservice.lib_async_tools import urlIsPdf
from typing import List, NamedTuple
import logging
logger = logging.getLogger(__name__)


class RVSCDE:
    country = 'BE'
    code = 'RSCE'
    data = []

    @staticmethod
    def docMatch(config, num):
        mask = re.compile('^\w{3}\.\d{1,6}$')
        return bool(mask.match(num))

    @staticmethod
    def getYears(config, _code):
        return RVSCDE.data.keys()

    @staticmethod
    async def getUrls(config, eclip, forceType=None):
        name = eclip.num.split('.')
        arr_num = name[1]
        urls = [{
            'rel': 'default',
            'href': f"http://www.raadvst-consetat.be/arr.php?nr={arr_num}"
        }, {
            'rel': 'pdf',
            'href': f"http://www.raadvst-consetat.be/arr.php?nr={arr_num}"
        }]

        if not forceType:
            return urls

        return lm.urlGetType(forceType, urls)

    @staticmethod
    def getCodes(config):
        return [RVSCDE.code]

    @staticmethod
    def checkYear(_config, year, _code):
        return year in RVSCDE.data.keys()

    @staticmethod
    def getDocuments(config: dict, code: str, year: int) -> List[str]:
        collection = []
        for record in RVSCDE.data[str(year)]:
            name = '{dtype}.{num}'.format(
                dtype=record['type'].upper(),
                num=record['num']
            )
            collection.append(name)

        return collection

    @staticmethod
    def getDocData(config, eclip):
        return {
            'logo': 'http://www.raadvst-consetat.be/a/s/logo.gif',
            'website': 'http://www.raadvst-consetat.be/',
            'court': RVSCDE.code,
            'source': 'RSCE',
            'year': eclip.year,
            'decision': eclip.num,
        }

    @staticmethod
    def init():
        """
        FIXME: This is purely experimental. Prepare some persistant storage for this.
        """
        data = {}
        with open('./resources/RVSCDE_def.json', 'r') as f:
            for line in f:
                rec = json.loads(line)
                index = str(rec['year'])
                if index in data:
                    data[index].append(rec)
                else:
                    data[index] = [rec]
        RVSCDE.data = data
