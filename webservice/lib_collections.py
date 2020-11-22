import json
import re
from webservice.lib_misc import parseECLI
from webservice.lib_async_tools import urlIsPdf
import logging
logger = logging.getLogger(__name__)

DEFAULT = 'default'
PDF = 'pdf'
META = 'meta'


def root(config):
    return [
        {'name': x['name'],
         'href': '/%s/' % (x['code']),
         'rel':''}
        for x in config['countries']
    ]


def sources():
    # FIXME: dirty, make cleaner ;)
    # XXX: Improvement: add params to do checks within this function
    # Instead of outside
    yield RVSCDE
    yield GHCC
    yield JUST


def getCourt(config, country, court):
    if country == 'BE' and court == 'RSCE':
        return RVSCDE
    if country == 'BE' and court == 'GHCC':
        return GHCC
    if country == 'BE':
        return JUST


def listCourts(config, country):
    codes = set()
    for source in sources():
        codes = codes.union(source.getCodes(config))
    cfg = config['ecli'][country]
    base = [
        {'name': cfg[x]['name'],
         'href': '/%s/%s/' % (country, x),
         'rel':''}
        for x in codes
    ]

    base = sorted(base, key=lambda x: x['name'])

    return base


def listYears(config, country, court):
    years = set()
    for source in sources():
        if court in source.getCodes(config):
            years = years.union(source.getYears(config, court))

    base = [
        {'name': y,
         'href': '/%s/%s/%s/' % (country, court, y),
         'rel': ''}
        for y in years
    ]

    base = sorted(base, key=lambda x: x['name'], reverse=True)

    return base


def listDocuments(config, country, court, year):
    docs = set()
    for source in sources():
        if court in source.getCodes(config) and year in source.getYears(config, court):
            docs = docs.union(source.getDocuments(config, court, year))

    result = [
        {'name': name,
         'href': '/%s/%s/%s/%s' % (
             JUST.country,
             court,
             year,
             name
         ),
         'rel': ''}
        for name in docs
    ]

    result = sorted(result, key=lambda x: x['name'], reverse=True)

    return result


def getECLICourt(config, ecli):
    if type(ecli) is str:
        ecli = parseECLI(ecli)

    if ecli.country != 'BE':
        return False

    if ecli.court in RVSCDE.getCodes(config) and RVSCDE.docMatch(config, ecli.num):
        logger.info('RVSCDE ECLI match')
        return RVSCDE

    if ecli.court in GHCC.getCodes(config) and GHCC.docMatch(config, ecli.num):
        logger.info('GHCC ECLI match')
        return GHCC

    if ecli.court in JUST.getCodes(config):
        return JUST

    return JUST


def urlGetType(ftype, urls):
    for url in urls:
        if url['rel'] == ftype:
            return url['href']
    return False


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
                ecli = parseECLI(line, True)
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

        return urlGetType(forceType, urls)

    @staticmethod
    def getCodes(config):
        return list(JUST.data.keys())

    @staticmethod
    def getYears(config, code):
        return JUST.data[code].keys()

    @staticmethod
    def checkYear(year, code):
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
    def getDocuments(config, code, year):
        return JUST.data[code][year]


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

        return urlGetType(forceType, urls)

    @staticmethod
    def getCodes(config):
        return [RVSCDE.code]

    @staticmethod
    def checkYear(year, _code):
        return year in RVSCDE.data.keys()

    @staticmethod
    def getDocuments(config, code, year):
        collection = []
        for record in RVSCDE.data[year]:
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

        return urlGetType(forceType, urls)

    @staticmethod
    def getCodes(config):
        return [GHCC.code]

    @staticmethod
    def checkYear(year, _code):
        return year in GHCC.data.keys()

    @staticmethod
    def getDocuments(config, code, year):
        collection = []
        for record in GHCC.data[year]:
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


for court in sources():
    court.init()
    court.init()
    court.init()
