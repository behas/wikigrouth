import os
import csv

from wikigrouth.wikipage import Wikipage


class Corpus:

    def __init__(self, seedfile, outputpath=None, override=False):
        print("***Initalizing corpus creation from seedfile", seedfile, "***")
        self.override = override
        if outputpath is None:
            self.outputpath = os.getcwd()
        else:
            self.outputpath = outputpath
        self.seedfile = seedfile
        self.uris = self._extract_uris(seedfile)
        if(len(self.uris) == 0):
            raise ValueError("Seedfile doesn't contain any uris.")
        else:
            print("Found", len(self.uris), "unique uris in seedfile.")

    def _extract_uris(self, seedfile):
        with open(seedfile, 'r') as f:
            uris = f.readlines()
            return uris

    @property
    def htmlpath(self):
        return self.outputpath + '/html'

    @property
    def textpath(self):
        return self.outputpath + '/text'

    @property
    def indexfile(self):
        return self.outputpath + '/index.csv'

    @property
    def entityfile(self):
        return self.outputpath + '/entities.csv'

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
        if content is None:
            content = "EMPTY"
        with open(filename, 'w') as f:
            f.write(content)

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
                uri = uri.strip()
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
                    if(entity['uri'] in self.uris):
                        in_seed = 1
                    else:
                        in_seed = 0
                    entity_writer.writerow({'doc_id': index,
                                            'offset': entity['offset'],
                                            'text': entity['text'],
                                            'uri': entity['uri'],
                                            'in_seed': in_seed})
