# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Nemanja Hranisavljevic
# Contact: nemanja@ai4cps.com


from urllib.parse import unquote, urlsplit, urlunsplit
import datetime
from ai4cps.backend.datetime_utils import str_to_datetime

ROUTE_PREFIX = "/ai4cps/"
# Deprecated: the dashboard's old path. Its links keep working, as they are redirected to ROUTE_PREFIX.
DEPRECATED_ROUTE_PREFIX = "/selfx/"


def deprecated_route_redirect(url):
    """The ROUTE_PREFIX address of a link under DEPRECATED_ROUTE_PREFIX, with the rest of its path and its query;
    None for any other link. Browsers keep the fragment themselves, as the server never sees it."""
    parts = urlsplit(url)
    if parts.path != DEPRECATED_ROUTE_PREFIX.rstrip("/") and not parts.path.startswith(DEPRECATED_ROUTE_PREFIX):
        return None
    return urlunsplit(("", "", ROUTE_PREFIX + parts.path[len(DEPRECATED_ROUTE_PREFIX):], parts.query, ""))

def parse_url(pathname):  # , href):
    feature = unquote(pathname[1:])
    split_url = feature.split('/')
    system = split_url[1]
    user = split_url[2]
    feature = split_url[3]
    start = split_url[4]
    end = split_url[5]
    return system, user, feature, start, end


def check_date(date_string):
    try:
        str_to_datetime(date_string)
    except:
        return False
    return True


def construct_url(system, user, feature, start, end):
    url = f'{ROUTE_PREFIX}{system}/{user}/{feature}/{start}/{end}'
    return url


def construct_id(*args):
    return '-'.join(args).replace('_', '-').replace(' ', '-').replace('.', '-')


def get_today():
    return datetime.datetime.today().strftime('%Y-%m-%d')
