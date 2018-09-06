from random import choice
import re
from time import strptime, strftime

from util import hook, http


TWITTER_URL_TIMELINE = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
TWITTER_URL_TWEETS = 'https://api.twitter.com/1.1/search/tweets.json'
TWITTER_URL_STATUS = 'https://api.twitter.com/1.1/statuses/show.json'


def twitter_request(api_key, url, params=None):
    if not params:
        params = {}

    params['tweet_mode'] = 'extended'

    try:
        return http.get_json(url, oauth=True, oauth_keys=api_key, params=params)
    except http.HTTPError as e:
        errors = {
            400: 'bad request (ratelimited?)',
            401: 'unauthorized',
            403: 'forbidden',
            404: 'invalid user/id',
            500: 'twitter is broken',
            502: 'twitter is down ("getting upgraded")',
            503: 'twitter is overloaded (lol, RoR)',
            410: 'twitter shut off api v1.'
        }

        if e.code in errors:
            raise ValueError('error: ' + errors[e.code])

        raise ValueError('error: unknown %s' % e.code)


def get_tweet_by_id(api_key, id):
    return twitter_request(api_key, TWITTER_URL_TIMELINE, { 'id': id })


def get_tweet_by_username(api_key, username, index=None):
    response = twitter_request(api_key, TWITTER_URL_TIMELINE, {'screen_name': username})

    if not 'statuses' in response:
        return None

    tweets = response["statuses"]

    if index is None:
        index = 0

    if index not in tweets:
        return None

    return tweets[index]


def get_tweet_by_search_term(api_key, search_term, index=None):
    response = twitter_request(api_key, TWITTER_URL_TIMELINE, {'q': search_term})


    if 'statuses' not in response:
        return None

    tweets = response["statuses"]

    if index is None:
        return choice(tweets)

    if index not in tweets:
        return None

    return tweets[index]


def format_tweet(tweet):
    if "retweeted_status" in tweet:
        rt = tweet["retweeted_status"]
        rt_text = http.unescape(rt["full_text"]).replace('\n', ' ')
        text = "RT @%s %s" % (rt["user"]["screen_name"], rt_text)
    else:
        text = http.unescape(tweet["full_text"]).replace('\n', ' ')

    screen_name = tweet["user"]["screen_name"]
    time = tweet["created_at"]

    time = strptime(time, '%a %b %d %H:%M:%S +0000 %Y')
    time = strftime("%Y-%m-%d %H:%M:%S", time)

    return "%s \x02%s\x02: %s" % (time, screen_name, text)


@hook.api_key('twitter')
@hook.command
def twitter(inp, api_key=None):
    ".twitter <user>/<user> <n>/<id>/#<search>/#<search> <n> -- " \
        "get <user>'s last/<n>th tweet/get tweet <id>/do <search>/get <n>th <search> result"

    if not isinstance(api_key, dict):
        return 'error: api keys not set'

    if any(key not in api_key for key in ('consumer', 'consumer_secret', 'access', 'access_secret')):
        return 'error: api keys not set'

    if re.match(r"^\d+$", inp):
        return format_tweet(get_tweet_by_id(inp))

    try:
        inp, index = re.split("\s+", inp, 1)
        index = int(index)

        if 0 > index >= 20:
            index = 0
    except ValueError:
        index = None
        inp += " " + index

    if re.match(r"^#", inp):
        tweet = get_tweet_by_search_term(api_key, inp, index)
    else:
        tweet = get_tweet_by_username(api_key, inp, index)

    return format_tweet(tweet)


@hook.api_key('twitter')
@hook.regex(r'https?://(mobile\.)?twitter.com/(#!/)?([_0-9a-zA-Z]+)/status/(?P<id>\d+)')
def show_tweet(match, api_key=None):
    return twitter(match.group('id'), api_key)
