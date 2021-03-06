import requests
import urllib
import logging
import ssl
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def tika_extract(config, url):
    """
    Extract text from provided file
    """
    tika_server = f"http://{config['tikaserver']}/rmeta/form"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(url, timeout=3, context=ctx) as response:
            r = requests.post(
                tika_server,
                # files={rawFile.filename: rawFile.file.read()}
                files={'upload': response.read()},
                headers={'Accept': 'application/json'}
                # headers={'Accept': 'text/plain'}
            )

        if r.status_code == 200:
            response = r.json()[0]
            # print(json.dumps(response, indent=2))
            rawText = response.get('X-TIKA:content', 'none')
            htmlText = rawText.replace('\n', '').encode('ascii', 'xmlcharrefreplace')
            # print(htmlText)

            soup = BeautifulSoup(rawText, 'html5lib')
            body = soup.find('body')
            # body = soup.find('div', {'class': 'page'})
            # print('-----------------')
            # print('-----------------')
            # print(body.text)
            # print('-----------------')
            # print('-----------------')
            mdText = body.text

            # rawFile.file.seek(0, 2)
            return {
                # "file_size": len(rawFile),
                # "filename": rawFile.filename,
                # "content_type": rawFile.content_type,
                # "size_bytes": rawFile.file.tell(),
                "html": htmlText.strip(),
                "markdown": mdText.strip(),
                'plaintext': rawText.strip(),
            }

        raise RuntimeError("Failed to extract text from file")

    except Exception as e:
        logger.exception(e)
        raise RuntimeError("Failed to contact server %s", tika_server)


async def urlIsPdf(url):
    r = requests.head(url, verify=False)
    return 'application/pdf' in r.headers.get('content-type')
