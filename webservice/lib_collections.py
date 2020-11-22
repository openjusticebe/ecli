from webservice.lib_misc import parseECLI
import logging
from webservice.sources import GHCC
from webservice.sources import JUST
from webservice.sources import RVSCDE
from webservice.sources import OPENJUSTICE
logger = logging.getLogger(__name__)

DEFAULT = 'default'
PDF = 'pdf'
META = 'meta'


def sources():
    # FIXME: dirty, make cleaner ;)
    # XXX: Improvement: add params to do checks within this function
    # Instead of outside
    yield RVSCDE
    yield GHCC
    yield OPENJUSTICE
    yield JUST


for court in sources():
    court.init()
    court.init()
    court.init()


def root(config):
    return [
        {'name': x['name'],
         'href': '/%s/' % (x['code']),
         'rel':''}
        for x in config['countries']
    ]


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
            docs = docs.union(source.getDocuments(config, court, int(year)))

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

    if ecli.court in OPENJUSTICE.getCodes(config) and OPENJUSTICE.docMatch(config, ecli.num):
        logger.info('OPENJUSTICE ECLI match')
        return OPENJUSTICE

    if ecli.court in JUST.getCodes(config):
        return JUST

    return JUST



