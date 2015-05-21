import os
import re
import csv

from wikigrouth.wikipage import Wikipage


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