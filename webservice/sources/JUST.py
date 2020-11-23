from webservice.lib_async_tools import urlIsPdf
import webservice.lib_misc as lm
from typing import List
import logging
logger = logging.getLogger(__name__)


class JUST:
    country = 'BE'
    data = []

    @staticmethod
    def init():
        """
        FIXME: This is purely experimental. Prepare some persistant storage for this.
        {"num": 208168, "year": 2010, "language": "french", "type": "arr"}
        {"num": 72214, "year": 1998, "language": "dutch", "type": "arr"}
        """
        data = {}

        with open('./resources/IUBEL.txt', 'r') as f:
            for line in f:
                ecli = lm.parseECLI(line, True)
                if ecli:
                    y = ecli.year
                    c = ecli.court
                    if c in data:
                        if y in data[c]:
                            if ecli.num not in data[c][y]:
                                data[c][y].append(ecli.num)
                        else:
                            data[c][y] = [ecli.num]
                    else:
                        data[c] = {y: [ecli.num]}

        JUST.data = data

    @staticmethod
    async def getUrls(config, eclip, forceType=None):
        # TODO: check if pdf exists
        # https://iubel.be/IUBELwork/ECLI:BE:AHANT:2004:ARR.20040604.5_NL.pdf
        urls = [
            {'rel': 'default', 'href': f"https://iubel.be/IUBELcontent/ViewDecision.php?id={eclip.raw}"},
            {'rel': 'meta', 'href': f"https://iubel.be/IUBELcontent/ViewDecision.php?id={eclip.raw}"}
        ]

        test_urls = [
            f"https://iubel.be/IUBELwork/{eclip.raw}_NL.pdf",
            f"https://iubel.be/IUBELwork/{eclip.raw}_FR.pdf",
        ]

        for url in test_urls:
            if await urlIsPdf(url):
                urls.append({'rel': 'pdf', 'href': url})

        if not forceType:
            return urls

        return lm.urlGetType(forceType, urls)

    @staticmethod
    def getCodes(config):
        return list(JUST.data.keys())

    @staticmethod
    def getYears(config, code):
        return JUST.data[code].keys()

    @staticmethod
    def checkYear(_config, year, code):
        return year in JUST.data[code].keys()

    @staticmethod
    def getDocData(config, eclip):
        return {
            'logo': 'https://www.rechtbanken-tribunaux.be/themes/custom/hoverech/logo.svg',
            'website': 'https://iubel.be/IUBELhome/welkom',
            'court': eclip.court,
            'year': eclip.year,
            'source': 'IUBEL',
            'decision': eclip.num,
        }

    @staticmethod
    def getDocuments(config: dict, code: str, year: int) -> List[str]:
        return JUST.data[code][str(year)]
