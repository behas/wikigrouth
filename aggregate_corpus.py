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


WIKI_INSTANCE = 'http://en.wikipedia.org'

def parse_concepts(skosfile):
    """Retuns a list of {pptid, dbpedia_uri} dictionaries."""
    r = re.compile(('<(.*)> '
                    '<http:\/\/www\.w3\.org\/2004\/02\/skos\/core#exactMatch> '
                    '<(.*)>'))
    concepts = []
    with open(skosfile, 'r') as f:
        for line in f:
            match = re.match(r, line)
            if match:
                s = match.group(1)
                o = match.group(2)
                pptid = os.path.basename(s)
                concepts.append({'pptid': pptid, 'dbpedia_uri': o})
    return concepts


def retrieve_wikipageid(dbpedia_uri):
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


def retrieve_wikipedia_page(page_id):
    API_URL = WIKI_INSTANCE + '/w/api.php'
    USER_AGENT = 'wikicorpus (https://github.com/behas/wikigrouth/)'
    params = {
        'action': 'query',
        'pageids': page_id,
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


def clean_wiki_page(soup):
    """
    Removes non-textual parts of page. Taken from:
    https://git.wikimedia.org/blob/mediawiki%2Fextensions%2FTextExtracts/46f6a992fa84f308f4990b6d4bdc337c07868d8c/TextExtracts.php
    """
    for tag in soup.find_all(['table', 'div', 'ul', 'li', 'tr', 'th']):
        tag.decompose()
    for tag in soup.find_all(class_=["mw-editsection",
                                     "error", "nomobile",
                                     "noprint", "noexcerpt"]):
        tag.decompose()
    for tag in soup.find_all('sup', 'reference'):
        tag.decompose()
    return soup


def extract_ne_mentions(wiki_page_html):
    """Extracts raw text and named entities from Wikipedia HTML page"""
    soup = BeautifulSoup(wiki_page_html)

    content = ""
    named_entities = []
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
                        link = WIKI_INSTANCE + element['href']
                        ne = {'offset': offset, 'text': text, 'link': link}
                        named_entities.append(ne)
                content += text
                offset += len(text)
            content += '\n'
            offset += 1
        if tag.name.startswith('h'):
            level = int(tag.name[1])
            h = '=' * level + ' ' + tag.get_text() + ' ' + '=' * level + '\n\n'
            content += h
            offset += len(h)
    return (content, named_entities)


def aggregate_corpus(skosfile, override=False):
    """Main corpus aggregation workflow function."""
    print("Parsing DBPedia concepts from", skosfile)
    concepts = parse_concepts(skosfile)
    if len(concepts) == 0:
        print("No concepts found. Aborting.")
        return
    outputpath = skosfile[:-3]
    # Preparations
    print("Preparing output path", outputpath)
    if not os.path.exists(outputpath):
        os.makedirs(outputpath)
    index_csv = outputpath + ".csv"
    ne_csv = outputpath + "_entities.csv"
    # Running aggregation procedure
    with open(index_csv, 'w') as i_csv, open(ne_csv, 'w') as ne_csv:
        # preparing CSV writers
        i_fields = ['pptid', 'dbpedia_uri', 'txt_file', 'html_file']
        i_writer = csv.DictWriter(i_csv, fieldnames=i_fields)
        i_writer.writeheader()
        ne_fields = ['doc_id', 'offset', 'text', 'link']
        ne_writer = csv.DictWriter(ne_csv, fieldnames=ne_fields)
        ne_writer.writeheader()
        for concept in concepts:
            print("\nProcessing concept", concept['pptid'], "...")
            outputpath_text = outputpath + '/txt'
            if not os.path.exists(outputpath_text):
                os.makedirs(outputpath_text)
            outputpath_html = outputpath + '/html'
            if not os.path.exists(outputpath_html):
                os.makedirs(outputpath_html)
            text_file = outputpath_text + '/' + concept['pptid'] + ".txt"
            html_file = outputpath_html + '/' + concept['pptid'] + ".html"
            if os.path.exists(text_file) or os.path.exists(html_file):
                if not override:
                    print("Files already aggregated")
                    continue
            print("Retrieving wikiPageID from", concept['dbpedia_uri'], "...")
            wikiPageID = retrieve_wikipageid(concept['dbpedia_uri'])
            print("Retrieving Wikipedia page", wikiPageID, "...")
            page_html = retrieve_wikipedia_page(wikiPageID)
            print("Extracting raw text and named entities...")
            content, named_entities = extract_ne_mentions(page_html)
            print("Found", len(named_entities), "named entity mentions.")
            # writing html and txt content
            with open(text_file, "w") as out_file:
                out_file.write(content)
                concept['txt_file'] = os.path.basename(text_file)
            with open(html_file, "w") as out_file:
                out_file.write(page_html)
                concept['html_file'] = os.path.basename(html_file)
            i_writer.writerow(concept)
            # writing extracted named entities
            for entity in named_entities:
                entity['doc_id'] = concept['pptid'] + ".txt"
                ne_writer.writerow(entity)


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
