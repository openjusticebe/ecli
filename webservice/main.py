#!/usr/bin/env python3
import argparse
import json
import logging
import math
import os
import sys
import uuid
import yaml
import pytz
import uvicorn
from fastapi import Depends, FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, IPvAnyAddress, Json, PositiveInt
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from datetime import datetime
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

# ############################################################### SERVER ROUTES
# #############################################################################
@app.on_event("startup")
async def startup_event():
    pass
    # FIXME: add future db support
    # global DB_POOL  # pylint:disable=global-statement
    # if os.getenv('NO_ASYNCPG', 'false') == 'false':
    #     DB_POOL = await asyncpg.create_pool(**config['postgresql'])

@app.get("/{rawEcli}")
def ecli(rawEcli):
    ecli = rawEcli.split(':')
    logger.info(f"{ecli}")
    logger.info(ecli)
    try:
        assert(ecli[0] == 'ECLI')
        assert(ecli[1] == 'BE')
    except AssertionError:
        raise HTTPException(status_code=400, detail="Item not found")

    if ecli[2] == 'RVSCDE':
        arr_num = ecli[4].replace('.','')
        return RedirectResponse(f"http://www.raadvst-consetat.be/arr.php?nr={arr_num}")

    if ecli[2] == 'CC':
        url = f"https://www.const-court.be/public/f/{ecli[3]}/{ecli[3]}-{ecli[4]}f.pdf"
        return RedirectResponse(url)

    url = f"https://iubel.be/IUBELcontent/ViewDecision.php?id={rawEcli}"
    return RedirectResponse(url)

@app.get("/status")
def status():
    """
    Query service status
    """
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

# ##################################################################### STARTUP
# #############################################################################
def main():
    parser = argparse.ArgumentParser(description='ECLI server process')
    parser.add_argument('--config', dest='config', help='config file', default=None)
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Debug mode')
    args = parser.parse_args()
    if args.debug:
        logger.debug('Debug activated')
        config['log_level'] = 'debug'
        config['server']['log_level'] = 'debug'
        logger.debug('Arguments: %s', args)

    uvicorn.run(
        app,
        **config['server']
    )


if __name__ == "__main__":
    main()
