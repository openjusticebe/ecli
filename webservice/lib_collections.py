import json
import re
from webservice.lib_misc import parseECLI
from webservice.lib_async_tools import urlIsPdf

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


def country(config, country):
    codes = RVSCDE.getCodes(config) + GHCC.getCodes(config) + JUST.getCodes(config)
    cfg = config['ecli'][country]
    base = [
        {'name': cfg[x]['name'],
         'href': '/%s/%s/' % (country, x),
         'rel':''}
        for x in codes
    ]

    # for code in JUST.getCodes(config):
    #     base.append({
    #         'name': code,
    #         'href': '%s/%s/%s/' % (config['root'], country, code),
    #         'rel':''
    #     })

    return base


def getCourt(config, country, court):
    if country == 'BE' and court == 'RVSCDE':
        return RVSCDE
    if country == 'BE' and court == 'GHCC':
        return GHCC
    if country == 'BE':
        return JUST


def getECLICourt(config, ecli):
    if type(ecli) is str:
        ecli = parseECLI(ecli)

    if ecli.country != 'BE':
        return False

    if ecli.court in RVSCDE.getCodes(config):
        return RVSCDE

    if ecli.court in GHCC.getCodes(config):
        return GHCC

    if ecli.court in JUST.getCodes(config):
        return JUST

    return False


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
        return [
            {'name': x,
             'href': '/%s/%s/%s/' % (JUST.country, code, x),
             'rel': ''}
            for x in JUST.data[code].keys()

        ]

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
            'decision': eclip.num,
        }

    @staticmethod
    def getDocuments(config, code, year):
        collection = []
        for name in JUST.data[code][year]:
            ecli = f"ECLI:{JUST.country}:{code}:{year}:{name}"

            collection.append({
                'name': name,
                'href': '/%s/%s/%s/%s' % (
                    JUST.country,
                    code,
                    year,
                    name
                ),
                'rel': ''
            })

        return collection


class RVSCDE:
    country = 'BE'
    code = 'RVSCDE'
    data = []

    @staticmethod
    def getYears(config, _code):
        return [
            {'name': x,
             'href': '/%s/%s/%s/' % (RVSCDE.country, RVSCDE.code, x),
             'rel': ''}
            for x in RVSCDE.data.keys()
        ]

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
            ecli = f"ECLI:{RVSCDE.country}:{RVSCDE.code}:{year}:{name}"
            collection.append({
                'name': name,
                'href': '/%s/%s/%s/%s' % (
                    RVSCDE.country,
                    code,
                    year,
                    name
                ),
                'rel': ''
            })

        return collection

    @staticmethod
    def getDocData(config, eclip):
        return {
            'logo': 'http://www.raadvst-consetat.be/a/s/logo.gif',
            'website': 'http://www.raadvst-consetat.be/',
            'court': RVSCDE.code,
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
    def getYears(config, _code):
        return [
            {'name': x,
             'href': '/%s/%s/%s/' % (GHCC.country, GHCC.code, x),
             'rel': ''}
            for x in GHCC.data.keys()
        ]

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
            ecli = f"ECLI:{GHCC.country}:{GHCC.code}:{year}:{name}"

            collection.append({
                'name': name,
                'href': '/%s/%s/%s/%s' % (
                    GHCC.country,
                    code,
                    year,
                    name
                ),
                'rel': ''
            })

        return collection

    @staticmethod
    def getDocData(config, eclip):
        return {
            'logo': 'https://www.const-court.be/images/titre_index3.gif',
            'website': 'https://www.const-court.be/',
            'court': GHCC.code,
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


RVSCDE.init()
GHCC.init()
JUST.init()
