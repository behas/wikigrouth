from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString

import os
import requests
import urllib


class Wikipage:

    WIKI_INSTANCE = 'http://en.wikipedia.org'

    def __init__(self, uri, html_file=None):
        if(html_file is not None):
            self.html = self._load_from_file(html_file)
        else:
            self.html = self._load_from_wikipedia(uri)
        self.text, self.entities = self._process_page(self.html)

    def _process_page(self, page_html):
        """Extracts raw text and named entities from Wikipedia HTML page"""
        soup = BeautifulSoup(page_html, 'html.parser')
        soup = self.clean_wiki_page(soup)

        content = ""
        entities = []
        offset = 0

        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5']):
            contents = tag.contents
            if(contents is None or len(contents) == 0):
                continue
            # handle paragraphs
            if tag.name == 'p':
                for element in contents:
                    text = ""
                    if(type(element) is NavigableString):
                        text = str(element)
                    if(type(element) is Tag):
                        text += element.get_text()
                        if(element.name == 'a' and 'href' in element.attrs):
                            uri = Wikipage.WIKI_INSTANCE + element['href']
                            ne = {'offset': offset, 'text': text, 'uri': uri}
                            entities.append(ne)
                    content += text
                    offset += len(text)
                content += '\n'
                offset += 1
            if tag.name.startswith('h'):
                level = int(tag.name[1])
                dashes = '=' * level
                h = dashes + ' ' + tag.get_text() + ' ' + dashes + '\n\n'
                content += h
                offset += len(h)
        return (content, entities)

    def clean_wiki_page(self, soup):
        """Removes non-textual parts of page."""
        for tag in soup.find_all(['table', 'div', 'ul', 'li', 'tr', 'th']):
            tag.decompose()
        for tag in soup.find_all(class_=["mw-editsection",
                                         "error", "nomobile",
                                         "noprint", "noexcerpt"]):
            tag.decompose()
        for tag in soup.find_all('sup', 'reference'):
            tag.decompose()
        return soup

    def _load_from_file(self, html_file):
        print("Loading page from cache", html_file)
        page_html = None
        with open(html_file, 'r') as f:
            page_html = f.read()
        return page_html

    def _load_from_wikipedia(self, uri):
        print("Loading page from Wikipedia...")

        if uri.endswith("/"):
            uri = uri[:-1]
        title = os.path.basename(uri).strip()
        title = urllib.parse.unquote(title)

        API_URL = Wikipage.WIKI_INSTANCE + '/w/api.php'
        USER_AGENT = 'wikicorpus (https://github.com/behas/wikigrouth/)'
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'revisions',
            'rvlimit': 1,
            'rvprop': 'content',
            'rvparse': False,
            'redirects': True,
            'format': 'json'
        }
        headers = {
            'User-Agent': USER_AGENT
        }
        r = requests.get(API_URL, params=params, headers=headers)
        print(r.url)
        if(r.status_code != 200):
            print("FAILURE. Request", r.url, "failed.")
            return None
        response = r.json()
        pages = response['query']['pages']
        page = next(iter(pages.values()))
        page_html = page['revisions'][0]['*']
        return page_html
