"""
wikigruth

A Python tool for creating coreference resolution ground truths from Wikipedia.

"""

from wikigrouth.corpus import Corpus


__author__ = 'Bernhard Haslhofer (bernhard.haslhofer@ait.ac.at)'
__copyright__ = 'Copyright 2015, Bernhard Haslhofer'
__license__ = "MIT"
__version__ = '0.1.1'

__all__ = ['aggregate_corpus']


def aggregate_corpus(seedfile, outputpath=None, override=False):
    corpus = Corpus(seedfile, outputpath, override)
    corpus.aggregate(override)
