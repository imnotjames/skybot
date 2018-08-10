import urlparse
from util import hook, http
import re


WIKI_SCP_URL_REGEX = r'http://www.scp-wiki.net/scp-[0-9]+.+'
WIKI_SEARCH_URL = 'http://www.scp-wiki.net/search:site/a/p/q/{query}'
WIKI_RANDOM_URL = 'http://www.scp-wiki.net/random:random-scp'
CENSORED_UNICODE = u'\u2588'
RESULT_NO_WIKI_FOUND = u'SCP-\u2588\u2588\u2588\u2588 is still classified.'


def get_matching_scp_url(query):
    """
    Gets the URL for an SCP that matches the query

    :param query: query to serach for
    :return: first URL which matches the query, or none if not found
    :rtype: string or none
    """
    query = '%s title:"SCP-"' % query

    search_url = WIKI_SEARCH_URL.format(query=http.quote_plus(query))

    html_document = http.get_html(search_url)

    url_elements = html_document.xpath('//div[@class="search-results"]//div[@class="url"]')

    # Look through each of the elements and verify that it matches a valid SCP URL.
    # Some of the pages that get matched aren't actually SCP pages.
    for url_element in url_elements:
        url = url_element.text_content().strip()
        if re.match(WIKI_SCP_URL_REGEX, url):
            return url

    return None


def get_random_scp_url():
    """
    Retrieves a random SCP URL from the SCP-Wiki's random URL page.

    :returns: a random SCP URL or none if the site doesn't provide one
    :rtype: string or none
    """

    # The random page includes an iframe in the page-content div,
    # which includes the randomly selected page as a URL fragment.
    # We need to find the matching iframe, parse the URL, and return
    # the fragment.

    try:
        html_document = http.get_html(WIKI_RANDOM_URL)
    except http.HTTPError:
        return None

    iframe_elements = html_document.xpath('//div[@id="page-content"]//iframe')

    if not iframe_elements:
        return None

    return urlparse.urlparse(iframe_elements[0].attrib['src']).fragment


def translate_section(section_name):
    """
    Translate a section "title" to the dictionary key to represent it

    :param section_name:
    :return:
    :rtype: str
    """
    section_name = section_name.lower()
    section_name = section_name.replace('#', 'number')
    section_name = re.sub('[^a-z0-9]', '_', section_name).strip('_')

    return section_name


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


def parse_scp(html_document):
    """
    Get a dictionary representing the SCP, including the item number, descriptions, and more.

    :param html_document: the input HTML document to parse.
    :return: a dictionary with section keys that were found in the document
    :rtype: dict or none
    """
    page_content_element = html_document.get_element_by_id('page-content')

    if page_content_element is None:
        return None

    paragraph_elements = page_content_element.xpath('p')

    if not paragraph_elements:
        return None

    sections = {}
    current_key = None

    # Each of the paragraph elements are either the start of a new section
    # or are a continuation of the previous section.
    for p in paragraph_elements:
        paragraph_text = p.text_content().strip()

        # To be the start of a new section, they must be prefixed by a `Strong`
        # element which serves as the section title. To make working with this
        # dictionary easier, section titles should be cleaned up to only be
        # alpha-numeric with underscores.
        if len(p) > 0 and p[0].tag == 'strong' and p[0].text_content()[-1] == ':':
                key_text = p[0].text_content()
                current_key = translate_section(key_text)
                paragraph_text = paragraph_text[len(key_text) + 1:].strip()

        # If no current key has been found yet, discard the buffer
        if not current_key:
            continue

        if current_key not in sections:
            sections[current_key] = paragraph_text
        else:
            # Continuations should be appended to the section for the previously found section.
            sections[current_key] += ' ' + paragraph_text

    # Set defaults to use when these elements haven't been found.
    sections.setdefault('item_number', u'SCP-%s' % (CENSORED_UNICODE * 4))
    sections.setdefault('object_class', CENSORED_UNICODE * 8)
    sections.setdefault('description', CENSORED_UNICODE * 16)
    sections.setdefault('short_description', truncate(sections.get('description'), 150))

    return sections


def get_random_scp():
    """
    Get an SCP randomly

    :return: the random SCP or none if one wasn't provided
    :rtype: dict or none
    """
    return get_scp_by_url(get_random_scp_url())


def get_matching_scp(query):
    """
    Get the SCP that best matches the query string given, and returns a dictionary if possible.

    :param query: the query string to search for
    :return: the matching SCP or none if one couldn't be found
    :rtype: dict or none
    """
    return get_scp_by_url(get_matching_scp_url(query))


def get_scp_by_url(url):
    """
    Get SCP sections for a URL to a given SCP article.

    :param url: The URL to fetch sections for.
    :return: a dictionary that represents the sections of an SCP article
    :rtype: dict or none
    """
    if not url:
        return None

    try:
        sections = parse_scp(http.get_html(url))
    except http.HTTPError:
        return None

    sections.setdefault('url', url)

    return sections


@hook.command(autohelp=False)
def scp(inp):
    """.scp [term] -- search SCP wiki for a specific term or get a random SCP."""
    if inp:
        scp_dict = get_matching_scp(inp)
    else:
        scp_dict = get_random_scp()

    if not scp_dict:
        return RESULT_NO_WIKI_FOUND

    return (
        u'\x02{item_number}\x02 - CLASS: \x02{object_class}\x02 - {short_description} - {url}'
    ).format(
        **scp_dict
    )


if __name__ == '__main__':
    print(scp('scp-835'))
    print(scp('doggy'))
    print(scp(''))