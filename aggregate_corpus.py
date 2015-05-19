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
import json
import csv

import requests



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
    API_URL = 'http://en.wikipedia.org/w/api.php'
    USER_AGENT = 'wikicorpus (https://github.com/behas/wikicorpus/)'
    params = {
        'action': 'query',
        'pageids': page_id,
        'prop': 'extracts|revisions',
        'rvlimit': 1,
        'rvprop': 'content',
        'rvparse': False,
        'explaintext': False,
        'redirects': True,
        'exsectionformat': 'wiki',
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
    page = next (iter (pages.values()))
    page_text = page['extract']
    page_html = page['revisions'][0]['*']
    return page_text, page_html


def aggregate_corpus(skosfile, override=False):
    """Main corpus aggregation workflow function."""
    print("Parsing DBPedia concepts from", skosfile)
    concepts = parse_concepts(skosfile)
    if len(concepts) == 0:
        print("No concepts found. Aborting.")
        return
    outputpath = skosfile[:-3]
    print("Preparing output path", outputpath)
    if not os.path.exists(outputpath):
                    os.makedirs(outputpath)
    csv_file = outputpath + ".csv"
    with open(csv_file, 'w') as csv_file:
        fieldnames = ['pptid', 'dbpedia_uri', 'txt_file', 'html_file']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for concept in concepts:
            print("\nProcessing concept", concept['pptid'], "...")
            text_file = outputpath + '/txt/' + concept['pptid'] + ".txt"
            html_file = outputpath + '/html/' + concept['pptid'] + ".html"
            if os.path.exists(text_file) or os.path.exists(html_file):
                if not override:
                    print("Files already aggregated")
                    continue
            print("Retrieving wikiPageID from", concept['dbpedia_uri'], "...")
            wikiPageID = retrieve_wikipageid(concept['dbpedia_uri'])
            print("Retrieving Wikipedia page", wikiPageID, "...")
            page_text, page_html = retrieve_wikipedia_page(wikiPageID)
            with open(text_file, "w") as out_file:
                out_file.write(page_text)
                concept['txt_file'] = os.path.basename(text_file)
            with open(html_file, "w") as out_file:
                out_file.write(page_html)
                concept['html_file'] = os.path.basename(html_file)
            writer.writerow(concept)


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
