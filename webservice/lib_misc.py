import yaml

def content_to_html(data):
    out = ['<!DOCTYPE html>\n<html lang="en"><body>']
    if 'status' in data:
        out.append("<pre>%s</pre>" % yaml.dump(data['status'], indent=2))

    if 'links' in data:
        out.append('<h2>Links :</h2>')
        out.append('<dl>')
        for link in data['links'] :
            out.append('<dt>{rel}</dt><dd><a href="{href}">{href}</a></dd>'.format(**link))
        out.append('</dl>')
    out.append('</body></html>')

    return "\n".join(out)

def content_to_plain(data):
    return "In construction"
