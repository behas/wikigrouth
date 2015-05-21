#!/usr/bin/env python
"""
Aggregates a corpus of Wikipedia documents from a given PPT corpus file.

Invocation:
$ python aggregate_corpus.py data/skos_file.nt
"""

import argparse
import os
import sys
import re
import csv

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


class Corpus:

    def __init__(self, seedfile, override=False):
        print("***Initalizing corpus creation from seedfile", seedfile, "***")
        self.override = override
        self.seedfile = seedfile
        self.uris = self._extract_uris(seedfile)
        if(len(self.uris) == 0):
            raise ValueError("Seedfile doesn't contain any uris.")
        else:
            print("Found", len(self.uris), "unique uris in seedfile.")

    def _extract_uris(self, seedfile):
        pattern = "<(http:\/\/dbpedia.org\/resource\/.*)>"
        uris = []
        with open(seedfile, 'r') as f:
            contents = f.read()
            uris = re.findall(pattern, contents)
        return list(set(uris))

    @property
    def outputpath(self):
        sep_index = self.seedfile.find('.')
        return self.seedfile[:sep_index]

    @property
    def htmlpath(self):
        return self.outputpath + '/html'

    @property
    def textpath(self):
        return self.outputpath + '/text'

    @property
    def indexfile(self):
        return self.outputpath + '.csv'

    @property
    def entityfile(self):
        return self.outputpath + '_entities.csv'

    def _ensurepaths(self):
        for path in [self.outputpath, self.htmlpath, self.textpath]:
            if not os.path.exists(path):
                print("Creating output path", path)
                os.makedirs(path)

    def htmlfile(self, uri):
        return self.htmlpath + '/' + os.path.basename(uri) + '.html'

    def textfile(self, uri):
        return self.textpath + '/' + os.path.basename(uri) + '.txt'

    def _write_file(self, filename, content, override=False):
        if(not override and os.path.exists(filename)):
            return
        with open(filename, 'w') as f:
            f.write(content)

    def to_dbpedia(self, wikipedia_uri):
        return wikipedia_uri.replace("en.wikipedia.org/wiki",
                                     "dbpedia.org/resource")

    def aggregate(self, override=False):
        self._ensurepaths()
        fieldnames_index = ['doc_id', 'uri', 'html_file', 'text_file']
        fieldnames_entity = ['doc_id', 'offset', 'text', 'uri', 'in_seed']
        with open(self.indexfile, 'w') as index_csv, \
                open(self.entityfile, 'w') as entity_csv:

            index_writer = csv.DictWriter(index_csv,
                                          fieldnames=fieldnames_index)
            index_writer.writeheader()
            entity_writer = csv.DictWriter(entity_csv,
                                           fieldnames=fieldnames_entity)
            entity_writer.writeheader()

            for index, uri in enumerate(self.uris):
                print("\nProcessing uri", uri, "...")
                if(os.path.exists(self.htmlfile(uri)) and not override):
                    page = Wikipage(uri, self.htmlfile(uri))
                else:
                    page = Wikipage(uri)
                self._write_file(self.htmlfile(uri), page.html, override)
                self._write_file(self.textfile(uri), page.text, True)
                # Recording output in CSV files
                html_file_rel = os.path.basename(self.htmlfile(uri))
                text_file_rel = os.path.basename(self.textfile(uri))
                index_writer.writerow({'doc_id': index,
                                       'uri': uri,
                                       'html_file': html_file_rel,
                                       'text_file': text_file_rel})
                for entity in page.entities:
                    entity_uri = self.to_dbpedia(entity['uri'])
                    if(entity_uri in self.uris):
                        in_seed = 1
                    else:
                        in_seed = 0
                    entity_writer.writerow({'doc_id': index,
                                            'offset': entity['offset'],
                                            'text': entity['text'],
                                            'uri': entity_uri,
                                            'in_seed': in_seed})


def aggregate_corpus(seedfile, override=False):
    corpus = Corpus(seedfile)
    corpus.aggregate(override)


parser = argparse.ArgumentParser(
                    description="Aggregate corpus from given SKOS file.")
parser.add_argument('skosfile', type=str, nargs=1,
                    help="The input SKOS file.")
parser.add_argument('-f', '--force', action='store_true',
                    help="Force override")


if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()
aggregate_corpus(args.skosfile[0], args.force)
