import re
import yaml
import json
from collections import namedtuple
import logging
logger = logging.getLogger(__name__)
ECLI_MASK = re.compile(r'ECLI:(?P<country>\w*):(?P<code>\w*):(?P<year>\d*):(?P<id>.*)$')
ECLI = namedtuple('ECLI', ['country', 'court', 'year', 'num', 'raw'])


def content_to_html(config, data):
    out = ['<!DOCTYPE html>\n<html lang="en"><body>']
    out.append('<style>.row { display: flex} .column { flex: 50%; } .warning { color: red } .info { color: green } pre { font-family: monospace }</style>')
    out.append('<p class="warning">⚠ What you are seeing is raw technical data formatted in a human readable way. It is not meant to be user-friendly. To access a more user-friendy service, please access to <a href="http://omdat.openjustice.lltl.be/">Omdat</a></p>')
    self = False
    if 'title' in data:
        out.append('<h1>%s</h1>' % data['title'])
    out.append('<div class="row">')

    out.append('<div class="column">')

    if 'links' in data:
        out.append('<h2>Links</h2>')
        out.append('<dl>')
        for link in data['links']:
            out.append('<dt>{rel}</dt><dd><a href="{href}">{href}</a></dd>'.format(**link))
            if link['rel'] == 'self':
                self = '%s%s' % (config['root'], link['href'])
        out.append('</dl>')

    if 'content' in data:
        out.append('<h2>Content</h2>')

        dc = data['content']
        if 'data' in dc:
            out.append('<h3>data :</h3>')
            dd = dc['data']

            if 'logo' in dd:
                out.append('<img src="%s" style="max-width:250px"/><br />' % dd['logo'])

            if 'website' in dd and 'court' in dd:
                out.append('<a href="{url}">{name}</a>'.format(
                    url=dd['website'],
                    name=dd['court']
                ))

        if 'links' in dc:
            out.append('<h3>Links</h3>')
            out.append('<dl>')
            for link in dc['links']:
                out.append('<dt>{rel}</dt><dd><a href="{href}" rel="nofollow" target="_blank">{href}</a></dd>'.format(**link))
            out.append('</dl>')

    if 'collection' in data:
        out.append('<h2>Collection</h2>')
        out.append('<dl>')
        for link in data['collection']:
            out.append('<dt>{name}</dt><dd><a href="{href}" rel="{rel}">{href}</a></dd>'.format(**link))
        out.append('</dl>')
    out.append('</div>')

    out.append('<div class="column">')
    out.append('<div class="box"><h2>JSON preview</h2>')
    out.append('<p>Set "application/json" in your request\'s Accept header to get the result below.</p>')
    if self:
        out.append(f'<pre class="info">curl {self} -H "Accept: application/json"</pre>')

    out.extend(['<pre>', json.dumps(data, indent=2), '</pre>'])
    out.append('</div>')
    out.append('</div>')

    out.append('</body></html>')

    return "\n".join(out)


def content_to_plain(data):
    return "In construction"


def parseECLI(ecli, noException=False):
    m = ECLI_MASK.match(ecli)
    if not m:
        if noException:
            return False
        else:
            logger.debug("Bad ecli: %s", ecli)
            raise RuntimeError("Bad ECLI")
    return ECLI(m.group('country'), m.group('code'), m.group('year'), m.group('id'), ecli)


def buildECLI(country, code, year, num):
    return parseECLI(f"ECLI:{country}:{code}:{year}:{num}")


def urlGetType(ftype, urls):
    for url in urls:
        if url['rel'] == ftype:
            return url['href']
    return False
