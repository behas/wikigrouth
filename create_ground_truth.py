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


# Regex matching linked DBpedia concepts in source file
R = "<(.*)> <http:\/\/www\.w3\.org\/2004\/02\/skos\/core#exactMatch> <(.*)>"
r = re.compile(R)

# 

WIKIPAGEID = "http://dbpedia.org/ontology/wikiPageID"

OUTPUTDIR = "data/"


def concepts(data):
     for line in data:
        match = re.match(r, line)
        if match:
            s = match.group(1)
            o = match.group(2)
            yield(s,o)

def aggregate_corpus(skosfile):
    with open(skosfile, 'r') as f:
        data = f.readlines()
        for pptid, dbpedia_uri in concepts(data):
            pptid = os.path.basename(pptid)
            # Find Wikipedia page id
            dbpedia_uri_json = dbpedia_uri.replace("resource", "data")
            dbpedia_uri_json += ".json"
            print("Querying", dbpedia_uri_json, "for Wikipedia page id...")
            r = requests.get(dbpedia_uri_json)
            wiki_article_id = None
            if(r.status_code != 200):
                print("FAILURE. Request", dbpedia_uri, "failed.")
            else:
                result = r.json()
                resource = result.get(dbpedia_uri)
                if not resource:
                    continue
                page_id = resource.get(WIKIPAGEID)
                if not page_id:
                    continue
                wiki_article_id = page_id[0]['value']
                pg = wikipedia.page(None, wiki_article_id)
                outputsubdir = os.path.basename(skosfile)[:-3]
                outputdir = OUTPUTDIR + outputsubdir + "/"
                if not os.path.exists(outputdir):
                    os.makedirs(outputdir)
                with open(outputdir + pptid + ".txt", "w") as out_file:
                    out_file.write(pg.content)
                with open(outputdir + pptid + ".html", "w") as out_file:
                    out_file.write(pg.html())
            print(pptid, dbpedia_uri, wiki_article_id)



parser = argparse.ArgumentParser(
                    description="Aggregate corpus from given SKOS file.")
parser.add_argument('skosfile', type=str, nargs=1,
                    help="The input SKOS file.")


if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()
aggregate_corpus(args.skosfile[0])
