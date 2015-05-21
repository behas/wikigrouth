from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString

import requests


class Wikipage:

    # TODO: remove DBPedia dependency and use Wikipedia export page instead

    WIKI_INSTANCE = 'http://en.wikipedia.org'

    def __init__(self, uri, html_file=None):
        if(html_file is not None):
            self.html = self._load_from_file(html_file)
        else:
            self.html = self._load_from_wikipedia(uri)
        self.text, self.entities = self._process_page(self.html)

    def _process_page(self, page_html):
        """Extracts raw text and named entities from Wikipedia HTML page"""
        soup = BeautifulSoup(page_html)
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
        if('dbpedia' not in uri):
            raise NotImplemented("Cannot process non-DBpedia seed uris.")
        wikipageID = self._retrieve_wikipageid(uri)
        page_html = self._retrieve_wikipedia_page(wikipageID)
        return page_html

    def _retrieve_wikipageid(self, dbpedia_uri):
        print("Retrieving wikiPageID from", dbpedia_uri, "...")
        dbpedia_uri_json = dbpedia_uri.replace("resource", "data")
        dbpedia_uri_json += ".json"
        r = requests.get(dbpedia_uri_json)
        if(r.status_code != 200):
            print("FAILURE. Request", r.url, "failed.")
            return None
        else:
            result = r.json()
            resource = result.get(dbpedia_uri)
            if not resource:
                return None
            page_id = resource.get("http://dbpedia.org/ontology/wikiPageID")
            if not page_id:
                return None
            return page_id[0]['value']

    def _retrieve_wikipedia_page(self, wikipageID):
        print("Retrieving Wikipedia page", wikipageID, "...")
        API_URL = Wikipage.WIKI_INSTANCE + '/w/api.php'
        USER_AGENT = 'wikicorpus (https://github.com/behas/wikigrouth/)'
        params = {
            'action': 'query',
            'pageids': wikipageID,
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
        if(r.status_code != 200):
            print("FAILURE. Request", r.url, "failed.")
            return None
        response = r.json()
        pages = response['query']['pages']
        page = next(iter(pages.values()))
        page_html = page['revisions'][0]['*']
        return page_html
