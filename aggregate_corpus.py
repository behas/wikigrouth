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
import wikipedia


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
        print("FAILURE. Request", dbpedia_uri, "failed.")
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


def aggregate_corpus(skosfile, override=False):
    """Main corpus aggregation workflow function."""
    print("Parsing DBPedia concepts from", skosfile)
    concepts = parse_concepts(skosfile)
    if len(concepts) == 0:
        print("No concepts found. Aborting.")
        return
    outputpath = outputsubdir = skosfile[:-3]
    print("Preparing output path", outputpath)
    if not os.path.exists(outputpath):
                    os.makedirs(outputpath)
    for concept in concepts:
        print("\nProcessing concept", concept['pptid'], "...")
        text_file = outputpath + '/' + concept['pptid'] + ".txt"
        html_file = outputpath + '/' + concept['pptid'] + ".html"
        if os.path.exists(text_file) or os.path.exists(html_file):
            if not override:
                print("Files already aggregated")
                continue
        print("Retrieving wikiPageID from", concept['dbpedia_uri'], "...")
        wikiPageID = retrieve_wikipageid(concept['dbpedia_uri'])
        print("Retrieving Wikipedia page", wikiPageID, "...")
        pg = wikipedia.page(None, wikiPageID)
        with open(text_file, "w") as out_file:
            out_file.write(pg.content)
        with open(html_file, "w") as out_file:
            out_file.write(pg.html())
        

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
