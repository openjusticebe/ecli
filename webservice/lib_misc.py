import yaml
import json

def content_to_html(data):
    out = ['<!DOCTYPE html>\n<html lang="en"><body>']
    if 'collection' in data:
        out.append('<h2>Collection :</h2>')
        out.append('<dl>')
        for link in data['collection'] :
            out.append('<dt>{name}</dt><dd><a href="{href}" rel="{rel}">{href}</a></dd>'.format(**link))
        out.append('</dl>')

    if 'links' in data:
        out.append('<h2>Links :</h2>')
        out.append('<dl>')
        for link in data['links'] :
            out.append('<dt>{rel}</dt><dd><a href="{href}">{href}</a></dd>'.format(**link))
        out.append('</dl>')

    if 'status' in data:
        out.append('<h2>Status :</h2>')
        out.append("<pre>%s</pre>" % yaml.dump(data['status'], indent=2))

    out.append('</body></html>')

    return "\n".join(out)

def content_to_plain(data):
    return "In construction"

def rvs_content():
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
    return data

