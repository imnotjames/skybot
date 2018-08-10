import re
from util import http, hook


TLDR_INDEX_URL = 'https://raw.githubusercontent.com/tldr-pages/tldr-pages.github.io/master/assets/index.json'
TLDR_PAGES_URL = 'https://raw.githubusercontent.com/tldr-pages/tldr/master/pages/{platform}/{command}.md'
PLATFORMS = ['common', 'linux', 'osx', 'windows', 'sunos']
WEB_VIEW_URL = 'https://tldr.ostera.io/{platform}/{command}'


def get_tldr_index():
    """
    Get the TLDR pages index file.

    :return: dict
    """
    return http.get_json(TLDR_INDEX_URL)


def find_matching_command(query, platform=None):
    """
    Find command that matches query with an optional platform filter.

    :param query: query to search through commands for
    :param platform: platform to filter on
    :return: returns a tuple with the first element being the platform, and the second the command
    :rtype: tuple
    """
    query = query.lower().strip()

    try:
        index = get_tldr_index()
    except http.HTTPError:
        return None, None

    for command in index['commands']:
        if query not in command['name']:
            continue

        if platform:
            if platform not in command['platform']:
                continue
        else:
            platform = command['platform'][0]

        return platform, command['name']

    return None, None


def get_tldr_page(platform, command):
    """
    Fetch a TLDR page by platform and command.

    :param platform: platform to retrieve
    :param command: command to retrieve
    :return: markdown of the
    """
    url = TLDR_PAGES_URL.format(platform=platform, command=command)

    return http.get(url)


def parse_tldr_page(platform, command, page_content):
    """
    Parse the page content and generate a dictionary representing this TLDR page.

    Dictionary has keys such as `url`, `command`, `platform`, `title`, and `short_description`.

    :param platform: platform of the page
    :param command: command of the page
    :param page_content: page content to parse in markdown format
    :return: dictionary representing the TLDR page
    :rtype: dict
    """
    page = {
        'command': command,
        'platform': platform
    }

    matches = re.match('# (.+)\n\n((> .+\n)+)', page_content)
    if matches:
        page['title'] = matches.group(1)
        page['short_description'] = matches.group(2)
    else:
        page['title'] = command
        page['short_description'] = 'No Description'

    if not platform == 'common':
        page['title'] = "%s: %s" % (platform, page['title'])

    page['short_description'] = re.sub('^> ', '', page['short_description'], flags=re.MULTILINE)
    page['short_description'] = page['short_description'].replace('\n', ' ').strip()

    page['url'] = WEB_VIEW_URL.format(**page)

    return page


def search_tldr_pages(query, platform=None):
    """
    Search the TLDR pages, with an optional platform.

    :param query: search query
    :param platform: platform to filter
    :return: dictionary with page information included, or None if not found
    :rtype: dict or none
    """
    platform, command = find_matching_command(query, platform=platform)

    if not command:
        return None

    page_content = get_tldr_page(platform, command)

    return parse_tldr_page(platform, command, page_content)


@hook.command
def tldr(inp):
    """
    .tldr [platform] [query] - query TLDR pages, optionally specifying a platform.

    :param inp:
    :return:
    """
    platform = None
    if ' ' in inp:
        platform, inp = inp.split(' ', 1)

        if platform not in PLATFORMS:
            return 'invalid platform'

    page = search_tldr_pages(inp, platform=platform)

    if not page:
        return 'not found'

    return '{title} - {short_description} - {url}'.format(**page)


if __name__ == '__main__':
    print(tldr('netstat'))
    print(tldr('osx netstat'))