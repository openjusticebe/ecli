import json
import re

def root(config):
    return [
        {'name' : x['name'],
         'href': '%s/ECLI/%s/' % (config['root'], x['code']),
         'rel':''}
        for x in config['countries']
    ]


def country(config, country):
    codes = RVSCDE.getCodes(config) + GHCC.getCodes(config) + JUST.getCodes(config)
    cfg = config['ecli'][country]
    base =  [
        {'name' : cfg[x]['name'],
         'href' : '%s/ECLI/%s/%s/' % (config['root'], country, x),
         'rel':''}
        for x in codes
    ]

    # for code in JUST.getCodes(config):
    #     base.append({
    #         'name': code,
    #         'href' : '%s/ECLI/%s/%s/' % (config['root'], country, code),
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
            mask = re.compile('ECLI:BE:(?P<code>\w*):(?P<year>\d*):(?P<id>.*)$')

            for line in f :
                m = mask.match(line)
                if m :
                    y = m.group('year')
                    c = m.group('code')
                    if c in data:
                        if y in data[c] :
                            if m.group('id') not in data[c][y]:
                                data[c][y].append(m.group('id'))
                        else:
                            data[c][y] = [m.group('id')]
                    else:
                        data[c] = {y : [m.group('id')]}

        JUST.data = data

    @staticmethod
    def getCodes(config):
        return list(JUST.data.keys())

    @staticmethod
    def getYears(config, code):
        return [
            {'name' : x,
             'href' : '%s/ECLI/%s/%s/%s/' % (config['root'], JUST.country , code, x),
             'rel':''}
            for x in JUST.data[code].keys()

        ]

    @staticmethod
    def checkYear(year, code):
        return year in JUST.data[code].keys()

    @staticmethod
    def getDocuments(config, code, year):
        collection = []
        for name in JUST.data[code][year]:
            ecli = f"ECLI:{JUST.country}:{code}:{year}:{name}"
            collection.append({
                'name': name,
                'href': '%s/%s' % (config['root'], ecli),
                'rel' : 'nofollow',
            })

        return collection


class RVSCDE:
    country = 'BE'
    code = 'RVSCDE'
    data = []

    @staticmethod
    def getYears(config, _code):
        return [
            {'name' : x,
             'href' : '%s/ECLI/%s/%s/%s/' % (config['root'], RVSCDE.country , RVSCDE.code, x),
             'rel':''}
            for x in RVSCDE.data.keys()
        ]

    @staticmethod
    def getCodes(config):
        return [RVSCDE.code]

    @staticmethod
    def checkYear(year, _code):
        return year in RVSCDE.data.keys()

    @staticmethod
    def getDocuments(config, _code, year):
        collection = []
        for record in RVSCDE.data[year]:
            name = '{dtype}.{num}'.format(
                dtype=record['type'].upper(),
                num=record['num']
            )
            ecli = f"ECLI:{RVSCDE.country}:{RVSCDE.code}:{year}:{name}"
            collection.append({
                'name': name,
                'href': '%s/%s' % (config['root'], ecli),
                'rel' : 'nofollow',
            })

        return collection

    @staticmethod
    def init():
        """
        FIXME: This is purely experimental. Prepare some persistant storage for this.
        """
        data = {}
        with open('./resources/RVSCDE_def.json', 'r') as f:
            for line in f :
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
            {'name' : x,
             'href' : '%s/ECLI/%s/%s/%s/' % (config['root'], GHCC.country , GHCC.code, x),
             'rel':''}
            for x in GHCC.data.keys()
        ]

    @staticmethod
    def getCodes(config):
        return [GHCC.code]

    @staticmethod
    def checkYear(year, _code):
        return year in GHCC.data.keys()

    @staticmethod
    def getDocuments(config, _code, year):
        collection = []
        for record in GHCC.data[year]:
            name = '{year}.{num}{lang}'.format(
                year=record['year'],
                num=record['num'],
                lang = 'f' if record['language'] == 'french' else 'n'
            )
            ecli = f"ECLI:{GHCC.country}:{GHCC.code}:{year}:{name}"
            collection.append({
                'name': name,
                'href': '%s/%s' % (config['root'], ecli),
                'rel' : 'nofollow',
            })

        return collection

    @staticmethod
    def init():
        """
        FIXME: This is purely experimental. Prepare some persistant storage for this.
        {"num": 208168, "year": 2010, "language": "french", "type": "arr"}
        {"num": 72214, "year": 1998, "language": "dutch", "type": "arr"}
        """
        data = {}
        with open('./resources/GHCC_def.json', 'r') as f:
            for line in f :
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
