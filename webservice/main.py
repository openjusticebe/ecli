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
from typing import Optional
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, IPvAnyAddress, Json, PositiveInt
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from datetime import datetime
from webservice.lib_misc import content_to_html, content_to_plain, rvs_content

sys.path.append(os.path.dirname(__file__))
VERSION = 1
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
    'root' : os.getenv('ROOT_DOMAIN', 'example.com'),
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

rvs_data = rvs_content()
logger.info('RVS rows: %s', len(rvs_data))

def status_get():
    now = datetime.now(pytz.utc)
    delta = now - START_TIME
    delta_s = math.floor(delta.total_seconds())
    return {
        'all_systems': 'nominal',
        'timestamp': now,
        'start_time': START_TIME,
        'uptime': f'{delta_s} seconds | {divmod(delta_s, 60)[0]} minutes | {divmod(delta_s, 86400)[0]} days',
        'api_version': VERSION,
        'api_counter': COUNTER,
    }


def negotiate(data, accept):
    # FIXME: Use fastapi router to implement proper content negotiation
    # https://github.com/tiangolo/fastapi/issues/521
    if 'text/html' in accept:
        return HTMLResponse(content_to_html(data), status_code=200)
    if 'application/json' in accept:
        return data
    # FIXME: Not so fast ! https://github.com/florimondmanca/msgpack-asgi
    # if 'application/msgpack' in accept:
    #     return msgpack.packb(data, use_bin_type=True)
    return PlainTextResponse(content_to_plain(data))

# ############################################################### SERVER ROUTES
# #############################################################################
@app.on_event("startup")
async def startup_event():
    pass
    # FIXME: add future db support
    # global DB_POOL  # pylint:disable=global-statement
    # if os.getenv('NO_ASYNCPG', 'false') == 'false':
    #     DB_POOL = await asyncpg.create_pool(**config['postgresql'])

@app.get("/{ECLI}")
def ecli(ECLI):
    """
    ECLI Demonstrator : access documents with their ECLI identifier by
    forwarding to the original document.

    Examples:

        * ECLI:BE:RVSCDE:2020:ARR.247760
        * ECLI:BE:CC:2020:141
        * ECLI:BE:CTLIE:2017:ARR.20170718.3
    """
    parts = ECLI.split(':')
    try:
        assert(parts[0] == 'ECLI')
        assert(parts[1] == 'BE')
    except AssertionError:
        raise HTTPException(status_code=400, detail="Item not found")

    if parts[2] == 'RVSCDE':
        name = parts[4].split('.')
        arr_num = name[1]
        return RedirectResponse(f"http://www.raadvst-consetat.be/arr.php?nr={arr_num}")

    if parts[2] == 'CC':
        url = f"https://www.const-court.be/public/f/{parts[3]}/{parts[3]}-{parts[4]}f.pdf"
        return RedirectResponse(url)

    url = f"https://iubel.be/IUBELcontent/ViewDecision.php?id={ECLI}"
    return RedirectResponse(url)


@app.get("/ECLI/")
def nav_ecli_root(accept: Optional[str] = Header(None)):
    """
    Navigation :

    Root of ECLI navigation : collection of available countries
    """
    collection = [{'name' : x['name'], 'href': '%s/ECLI/%s/' % (config['root'], x['code']), 'rel':''} for x in config['countries']]
    links = []
    links.append({ 'rel' : 'self', 'href' : "%s/ECLI/" % config['root'] })
    links.append({ 'rel' : 'documentation', 'href' : "https://eur-lex.europa.eu/content/help/faq/ecli.html"})

    response = {
        'status' : status_get(),
        'collection': collection,
        'links' : links,
        'content' : [
            {
                'url_template' : "%s/{COUNTRY}/" % config['root'],
                'placeholder' : '{COUNTRY}',
                'id': 'country_url_mask'
            },
        ]
    }

    return negotiate(response, accept)

@app.get("/ECLI/{COUNTRY}/")
def nav_ecli_country(COUNTRY, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Country navigation : collection of available court codes
    """

    collection = [{'name' : x['name'], 'href' : '%s/ECLI/%s/%s/' % (config['root'], COUNTRY, x['code']), 'rel':''}
        for x in config['ecli'][COUNTRY].values() ]

    links = []
    links.append({ 'rel' : 'self', 'href' : "%s/ECLI/%s/" % (config['root'], COUNTRY) })
    links.append({ 'rel' : 'parent', 'href' : "%s/ECLI/" % (config['root']) })

    response = {
        'status' : status_get(),
        'links' : links,
        'collection': collection,
        'content' : [
        ]
    }

    return negotiate(response, accept)


@app.get("/ECLI/{COUNTRY}/{CODE}/")
def nav_ecli_country(COUNTRY, CODE, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Country navigation : collection of available court codes
    """

    try:
        assert(COUNTRY == 'BE')
        assert(CODE == 'RVSCDE')
    except AssertionError:
        raise HTTPException(status_code=400, detail="Item not found")

    collection = [{'name' : x, 'href' : '%s/ECLI/%s/%s/%s/' % (config['root'], COUNTRY, CODE, x), 'rel':''}
        for x in rvs_data.keys() ]

    links = []
    links.append({ 'rel' : 'self', 'href' : "%s/ECLI/%s/%s/" % (config['root'], COUNTRY, CODE) })
    links.append({ 'rel' : 'parent', 'href' : "%s/ECLI/%s/" % (config['root'], COUNTRY) })

    response = {
        'status' : status_get(),
        'links' : links,
        'collection': collection,
        'content' : [
        ]
    }

    return negotiate(response, accept)


@app.get("/ECLI/{COUNTRY}/{CODE}/{YEAR}/")
def nav_ecli_country(COUNTRY, CODE, YEAR, accept: Optional[str] = Header(None)):
    """
    Navigation :

    Country navigation : collection of available court codes
    """

    try:
        assert(COUNTRY == 'BE')
        assert(CODE == 'RVSCDE')
        assert(YEAR in rvs_data)
    except AssertionError:
        raise HTTPException(status_code=400, detail="Item not found")

    collection = []
    for record in rvs_data[YEAR]:
        name = '{dtype}.{num}'.format(
            dtype=record['type'].upper(),
            num=record['num']
        )
        ecli = f"ECLI:{COUNTRY}:{CODE}:{YEAR}:{name}"
        collection.append({
            'name': name,
            'href': '%s/%s' % (config['root'], ecli),
            'rel' : 'nofollow',
            #'href': 'http://www.raadvst-consetat.be/arr.php?nr=%s' % record['num']
            #'href': '%s/ECLI/%s/%s/%s/%s/' % (config['root'], COUNTRY, CODE, YEAR, name)
        })

    links = []
    links.append({ 'rel' : 'self', 'href' : "%s/ECLI/%s/%s/%s/" % (config['root'], COUNTRY, CODE, YEAR) })
    links.append({ 'rel' : 'parent', 'href' : "%s/ECLI/%s/%s/" % (config['root'], COUNTRY, CODE) })

    response = {
        'status' : status_get(),
        'links' : links,
        'collection': collection,
        'content' : [
        ]
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


    ## XXX: Lambda is a hack : toml expects a callable
    if args.config :
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
