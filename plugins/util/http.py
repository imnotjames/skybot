import requests
from requests_oauthlib import OAuth1
from requests import HTTPError

from urllib import quote, unquote, quote_plus as _quote_plus

from lxml import etree, html


UA_SKYBOT = 'Skybot/1.0 https://github.com/rmmh/skybot'

jar = requests.cookies.RequestsCookieJar()


def _make_request(url, query_params=None, post_data=None, get_method=None, cookies=False, headers=None, oauth_keys=None, **kwargs):
    if query_params is None:
        query_params = {}

    query_params.update(kwargs)

    request = {
        'method': 'GET',
        'url': url,
        'params': {},
        'data': {},
        'headers': {
            'User-Agent': UA_SKYBOT
        }
    }

    if headers:
        request['headers'].update(headers)

    if query_params:
        request['params'].update(query_params)

    if post_data:
        request['data'].update(post_data)

    if oauth_keys:
        request['auth'] = OAuth1(
            client_key=oauth_keys.get('consumer'),
            client_secret=oauth_keys.get('consumer_secret'),
            resource_owner_key=oauth_keys.get('access'),
            resource_owner_secret=oauth_keys.get('access_secret')
        )

    if cookies:
        request['cookies']=jar

    if get_method is not None:
        request['method'] = get_method.upper()

    return requests.request(**request)


def get(*args, **kwargs):
    return _make_request(*args, **kwargs).text


def get_html(*args, **kwargs):
    return html.fromstring(_make_request(*args, **kwargs).text)


def get_xml(*args, **kwargs):
    return etree.fromstring(_make_request(*args, **kwargs).text)


def get_json(*args, **kwargs):
    return _make_request(*args, **kwargs).json()


def open(*args, **kwargs):
    return _make_request(*args, **kwargs).raw


def to_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf8', 'ignore')
    else:
        return str(s)


def quote_plus(s):
    return _quote_plus(to_utf8(s))


def unescape(s):
    if not s.strip():
        return s
    return html.fromstring(s).text_content()
