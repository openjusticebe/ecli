#!/usr/bin/env python3
import argparse
import json
import logging
import math
import os
import sys
import toml
import uuid
import yaml
import pytz
import uvicorn
import msgpack
import requests
from typing import Optional
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, IPvAnyAddress, Json, PositiveInt
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from datetime import datetime
from webservice.lib_misc import content_to_html, content_to_plain, parseECLI, buildECLI
import webservice.lib_async_tools as a_tools
import webservice.lib_collections as collections

sys.path.append(os.path.dirname(__file__))
VERSION = "0.1.1"
START_TIME = datetime.now(pytz.utc)
COUNTER = 0

# ################################################## SETUP AND ARGUMENT PARSING
# #############################################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())

config = {
    'postgresql': {
        'dsn': os.getenv('PG_DSN', 'postgres://user:pass@localhost:5432/db'),
        'min_size': 4,
        'max_size': 20
    },
    'server': {
        'host': os.getenv('HOST', '127.0.0.1'),
        'port': int(os.getenv('PORT', '5000')),
        'log_level': os.getenv('LOG_LEVEL', 'info'),
    },
    'log_level': os.getenv('LOG_LEVEL', 'info'),
    'proxy_prefix': os.getenv('PROXY_PREFIX', '/'),
    'root': os.getenv('ROOT_DOMAIN', 'example.com'),
    'tikaserver': os.getenv('TIKA_SERVER', '0.0.0.0:9998'),
}

if config['log_level'] == 'debug':
    logger.setLevel(logging.getLevelName('DEBUG'))

logger.debug('Debug activated')
logger.debug('Config values: \n%s', yaml.dump(config))

app = FastAPI(root_path=config['proxy_prefix'])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def status_get():
    now = datetime.now(pytz.utc)
    delta = now - START_TIME
    delta_s = math.floor(delta.total_seconds())
    return {
        'all_systems': 'nominal',
        'timestamp': str(now),
        'online_since': str(START_TIME),
        'online_for_seconds': delta_s,
        'api_version': VERSION,
        'api_counter': COUNTER,
    }


def negotiate(data, accept):
    # FIXME: Use fastapi router to implement proper content negotiation
    # https://github.com/tiangolo/fastapi/issues/521
    if 'text/html' in accept:
        return HTMLResponse(content_to_html(config, data), status_code=200)
    if 'application/json' in accept:
        return data
    # FIXME: Not so fast ! https://github.com/florimondmanca/msgpack-asgi
    # if 'application/msgpack' in accept:
    #     return msgpack.packb(data, use_bin_type=True)
    return PlainTextResponse(content_to_plain(data))


def count():
    # FIXME: this should rather become a decorator
    global COUNTER
    COUNTER += 1


# ############################################################### SERVER ROUTES
# #############################################################################
@app.on_event("startup")
async def startup_event():
    pass
    # FIXME: add future db support
    # global DB_POOL  # pylint:disable=global-statement
    # if os.getenv('NO_ASYNCPG', 'false') == 'false':
    #     DB_POOL = await asyncpg.create_pool(**config['postgresql'])


@app.get("/ecli/{ECLI}")
async def ecli(ECLI):
    """
    ECLI Demonstrator : access documents with their ECLI identifier by
    forwarding to the original document.

    Examples:

        * ECLI:BE:RVSCDE:2020:ARR.247760
        * ECLI:BE:GHCC:2020:2020.141f
        * ECLI:BE:CTLIE:2017:ARR.20170718.3
    """
    count()
    eclip = parseECLI(ECLI)
    logger.debug(eclip)
    court = collections.getECLICourt(config, eclip)
    url = await court.getUrls(config, eclip, collections.DEFAULT)
    return RedirectResponse(url)


@app.get("/txt/{ECLI}")
async def ecli(ECLI):
    """
    Non-negotiated plain text display

    Test with:
        * should work : ECLI:BE:RVSCDE:2020:ARR.247760
        * should work : ECLI:BE:GHCC:2020:2020.141f
        * Doesn't work (yet) : ECLI:BE:CTLIE:2017:ARR.20170718.3
    """
    count()

    eclip = parseECLI(ECLI)
    court = collections.getECLICourt(config, eclip)
    url = await court.getUrls(config, eclip, collections.PDF)
    if not await a_tools.urlIsPdf(url):
        raise HTTPException(status_code=412, detail=f"Document not available in this format, working on it !")
    data = await a_tools.tika_extract(config, url)
    if data and 'markdown' in data:
        return PlainTextResponse(data['markdown'])
    raise HTTPException(status_code=412, detail=f"Document not available in this format, working on it !")


@app.get("/html/{ECLI}")
async def ecli(ECLI):
    """
    Non-negotiated PDF display

    Test with:
        * should work : ECLI:BE:RVSCDE:2020:ARR.247760
        * should work : ECLI:BE:GHCC:2020:2020.141f
        * Doesn't work (yet) : ECLI:BE:CTLIE:2017:ARR.20170718.3
    """
    count()

    eclip = parseECLI(ECLI)
    court = collections.getECLICourt(config, eclip)
    url = await court.getUrls(config, eclip, collections.PDF)
    if not await a_tools.urlIsPdf(url):
        raise HTTPException(status_code=412, detail=f"Document not available in this format, working on it !")
    data = await a_tools.tika_extract(config, url)
    if data and 'html' in data:
        return HTMLResponse(data['html'])
    raise HTTPException(status_code=412, detail=f"Document not available in this format, working on it !")


@app.get("/pdf/{ECLI}")
async def ecli(ECLI):
    """
    Non-negotiated PDF display

    Test with:
        * should work : ECLI:BE:RVSCDE:2020:ARR.247760
        * should work : ECLI:BE:GHCC:2020:2020.141f
        * Doesn't work (yet) : ECLI:BE:CTLIE:2017:ARR.20170718.3
    """
    count()

    eclip = parseECLI(ECLI)
    court = collections.getECLICourt(config, eclip)
    url = await court.getUrls(config, eclip, collections.PDF)
    if not await a_tools.urlIsPdf(url):
        raise HTTPException(status_code=412, detail=f"Document not available in this format, working on it !")
    return RedirectResponse(url)


@app.get("/")
def nav_ecli_root(accept: Optional[str] = Header(None)):
    """
    Navigation :

    Root of ECLI navigation : collection of available countries
    """
    count()
    collection = collections.root(config)

    links = []
    links.append({'rel': 'self', 'href': "/"})

    response = {
        'status': status_get(),
        'collection': collection,
        'links': links,
        'content': {
            'links': [
                {'rel': 'ecli documentation', 'href': "https://eur-lex.europa.eu/content/help/faq/ecli.html"},
                {'rel': 'API documentation', 'href': "/docs"},
            ],
            'data':
            {
                'url_template': "/{COUNTRY}/",
                'placeholder': '{COUNTRY}',
                'id': 'country_url_mask'
            },
        }
    }

    return negotiate(response, accept)


@app.get("/{COUNTRY}/")
def nav_ecli_country(COUNTRY, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Country navigation : collection of available court codes
    """
    count()

    # Check if country is in supported country list
    if all(c['code'] != COUNTRY for c in config['countries']):
        raise HTTPException(status_code=400, detail=f"Country '{COUNTRY}' not available")

    links = []
    links.append({'rel': 'self', 'href': "/%s/" % (COUNTRY)})
    links.append({'rel': 'parent', 'href': "/"})
    links.append({'rel': 'root', 'href': "/"})

    response = {
        'status': status_get(),
        'links': links,
        'collection': collections.country(config, COUNTRY),
        'content': [
        ]
    }

    return negotiate(response, accept)


@app.get("/{COUNTRY}/{CODE}/")
def nav_ecli_court(COUNTRY, CODE, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Court navigation : collection of available years for a particular court
    """
    count()

    # Check if country is in supported country list
    if all(c['code'] != COUNTRY for c in config['countries']):
        raise HTTPException(status_code=400, detail=f"Country '{COUNTRY}' not available")

    # Check if code is in country supported court list
    if CODE not in config['ecli'][COUNTRY]:
        raise HTTPException(status_code=400, detail=f"Court '{CODE}' not available in '{COUNTRY}'")

    Court = collections.getCourt(config, COUNTRY, CODE)

    links = []
    links.append({'rel': 'self', 'href': "/%s/%s/" % (COUNTRY, CODE)})
    links.append({'rel': 'parent', 'href': "/%s/" % (COUNTRY)})
    links.append({'rel': 'root', 'href': "/"})

    response = {
        'status': status_get(),
        'links': links,
        'collection': Court.getYears(config, CODE),
        'content': [
        ]
    }

    return negotiate(response, accept)


@app.get("/{COUNTRY}/{CODE}/{YEAR}/")
def nav_ecli_year(COUNTRY, CODE, YEAR, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Year navigation : available documents for specified year
    """
    count()

    # Check if country is in supported country list
    if all(c['code'] != COUNTRY for c in config['countries']):
        raise HTTPException(status_code=400, detail=f"Country '{COUNTRY}' not available")

    # Check if code is in country supported court list
    if CODE not in config['ecli'][COUNTRY]:
        raise HTTPException(status_code=400, detail=f"Court '{CODE}' not available in '{COUNTRY}'")

    Court = collections.getCourt(config, COUNTRY, CODE)

    # Check if year is in court supported years list
    if not Court.checkYear(YEAR, CODE):
        raise HTTPException(status_code=400, detail=f"Year '{YEAR}' not available in '{COUNTRY}', Court '{CODE}'")

    links = []
    links.append({'rel': 'self', 'href': "/%s/%s/%s/" % (COUNTRY, CODE, YEAR)})
    links.append({'rel': 'parent', 'href': "/%s/%s/" % (COUNTRY, CODE)})
    links.append({'rel': 'root', 'href': "/"})

    response = {
        'status': status_get(),
        'links': links,
        'collection': Court.getDocuments(config, CODE, YEAR),
        'content': [
        ]
    }

    return negotiate(response, accept)


@app.get("/{COUNTRY}/{CODE}/{YEAR}/{NUM}")
async def nav_ecli_year(COUNTRY, CODE, YEAR, NUM, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Document data sheet : links to resources, metadata
    """
    count()

    eclip = buildECLI(COUNTRY, CODE, YEAR, NUM)

    # Check if country is in supported country list
    if all(c['code'] != COUNTRY for c in config['countries']):
        raise HTTPException(status_code=400, detail=f"Country '{COUNTRY}' not available")

    # Check if code is in country supported court list
    if CODE not in config['ecli'][COUNTRY]:
        raise HTTPException(status_code=400, detail=f"Court '{CODE}' not available in '{COUNTRY}'")

    Court = collections.getECLICourt(config, eclip)

    # Check if year is in court supported years list
    if not Court.checkYear(YEAR, CODE):
        raise HTTPException(status_code=400, detail=f"Year '{YEAR}' not available in '{COUNTRY}', Court '{CODE}'")

    links = []
    links.append({'rel': 'self', 'href': "/%s/%s/%s/%s" % (COUNTRY, CODE, YEAR, NUM)})
    links.append({'rel': 'parent', 'href': "/%s/%s/%s/" % (COUNTRY, CODE, YEAR)})
    links.append({'rel': 'root', 'href': "/"})

    docdata = Court.getDocData(config, eclip)

    urls = await Court.getUrls(config, eclip)
    content_links = []
    for url in urls:
        if url['rel'] == 'default':
            content_links.append({'rel': 'default', 'href': "/ecli/%s" % (eclip.raw)})
        if url['rel'] == 'pdf' and await a_tools.urlIsPdf(url['href']):
            content_links.append({'rel': 'pdf', 'href': "/pdf/%s" % (eclip.raw)})
            content_links.append({'rel': 'txt', 'href': "/txt/%s" % (eclip.raw)})
            content_links.append({'rel': 'html', 'href': "/html/%s" % (eclip.raw)})
        if url['rel'] == 'meta':
            content_links.append({'rel': 'meta', 'href': url['href']})

    response = {
        'status': status_get(),
        'links': links,
        'content': {
            'data': Court.getDocData(config, eclip),
            'links': content_links,
        }
    }

    return negotiate(response, accept)


@app.get("/status")
def status():
    """
    Query service status
    """
    return status_get()


# ##################################################################### STARTUP
# #############################################################################
def main():
    global config

    parser = argparse.ArgumentParser(description='ECLI server process')
    parser.add_argument('--config', dest='config', help='config file', default=None)
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Debug mode')
    args = parser.parse_args()

    # XXX: Lambda is a hack : toml expects a callable
    if args.config:
        t_config = toml.load(['config_default.toml', args.config])
    else:
        t_config = toml.load('config_default.toml')

    config = {**config, **t_config}

    if args.debug:
        logger.setLevel(logging.getLevelName('DEBUG'))
        logger.debug('Debug activated')
        config['log_level'] = 'debug'
        config['server']['log_level'] = 'debug'
        logger.debug('Arguments: %s', args)
        logger.debug('config: %s', yaml.dump(config, indent=2))
        logger.debug('config: %s', toml.dumps(config))

    uvicorn.run(
        app,
        **config['server']
    )


if __name__ == "__main__":
    main()
