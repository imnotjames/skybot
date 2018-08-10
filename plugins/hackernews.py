import unittest

from util import http, hook


HACKERNEWS_API_URL = 'https://hacker-news.firebaseio.com/v0/item/{item_id}.json'


def get_hackernews_entry(item_id):
    return http.get_json(HACKERNEWS_API_URL.format(item_id=int(item_id)))


def truncate(data, length=80, append='...'):
    """
    Truncate a string, appending an ellipsis if the string was shortened
    :param data: string to truncate
    :param append: string to append if truncation occurs, defaulting to '...'
    :param length: length to truncate to
    :return: truncated string
    :rtype: string
    """
    return data[:length-len(append)].strip() + append if len(data) > length else data


@hook.regex(r'(?i)https://(?:www\.)?news\.ycombinator\.com\S*id=(\d+)')
def hackernews(match):
    entry = get_hackernews_entry(match.group(1))

    if entry['type'] == "story":
        entry['title'] = truncate(http.unescape(entry['title']), length=200)
        return u"{title} by {by} with {score} points and {descendants} comments ({url})".format(**entry)

    if entry['type'] == "comment":
        entry['text'] = truncate(http.unescape(entry['text'].replace('<p>', ' // ')), length=300)
        return u'"{text}" -- {by}'.format(**entry)


class Test(unittest.TestCase):
    def news(self, inp):
        re = hackernews._hook[0][1][1]['re']
        return hackernews(re.search(inp))

    def test_story(self):
        assert 'Desalination' in self.news('https://news.ycombinator.com/item?id=9943431')

    def test_comment(self):
        res = self.news('https://news.ycombinator.com/item?id=9943987')
        assert 'kilowatt hours' in res
        assert 'oaktowner' in res

    def test_comment_encoding(self):
        res = self.news('https://news.ycombinator.com/item?id=9943897')
        assert 'abominations' in res
        assert '> ' in res  # encoding
