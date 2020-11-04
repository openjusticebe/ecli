import json

def root(config):
    return [
        {'name' : x['name'],
         'href': '%s/ECLI/%s/' % (config['root'], x['code']),
         'rel':''}
        for x in config['countries']
    ]


def country(config, country):
    return [
        {'name' : x['name'],
         'href' : '%s/ECLI/%s/%s/' % (config['root'], country, x['code']),
         'rel':''}
        for x in config['ecli'][country].values()
    ]

def getCourt(config, country, court):
    if country == 'BE' and court == 'RVSCDE':
        return RVSCDE
    if country == 'BE' and court == 'GHCC':
        return GHCC


class RVSCDE:
    country = 'BE'
    code = 'RVSCDE'
    data = []

    @staticmethod
    def getYears(config):
        return [
            {'name' : x,
             'href' : '%s/ECLI/%s/%s/%s/' % (config['root'], RVSCDE.country , RVSCDE.code, x),
             'rel':''}
            for x in RVSCDE.data.keys()
        ]

    @staticmethod
    def checkYear(year):
        return year in RVSCDE.data.keys()

    @staticmethod
    def getDocuments(config, year):
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

        {"num": 200874, "year": 2010, "language": "french", "type": "arr"}
        {"num": 142636, "year": 2005, "language": "dutch", "type": "arr"}
        {"num": 246073, "year": 2019, "language": "dutch", "type": "arr"}
        {"num": 208168, "year": 2010, "language": "french", "type": "arr"}
        {"num": 72214, "year": 1998, "language": "dutch", "type": "arr"}
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
    def getYears(config):
        return [
            {'name' : x,
             'href' : '%s/ECLI/%s/%s/%s/' % (config['root'], GHCC.country , GHCC.code, x),
             'rel':''}
            for x in GHCC.data.keys()
        ]

    @staticmethod
    def checkYear(year):
        return year in GHCC.data.keys()

    @staticmethod
    def getDocuments(config, year):
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

        {"num": 200874, "year": 2010, "language": "french", "type": "arr"}
        {"num": 142636, "year": 2005, "language": "dutch", "type": "arr"}
        {"num": 246073, "year": 2019, "language": "dutch", "type": "arr"}
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
