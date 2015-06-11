Wikigrouth - A Python tool for extracting entity mentions from a collection of Wikipedia documents.

## What is it good for?

Are you working on some coreference (or named entity) resolution task? Have you already reached the point of evaluating your solution? Then you probably know that you need some ground truth data set...and it is verly likely that you don't have it.

If you are looking for some large-scale and domain-independent data set, then you should look into [Wikilinks][wikilinks].

If you are working on some domain-specific task (e.g., sports, medicine, etc.), then Wikigrouth could be your solution. It takes a file containing Wikipedia or DBpedia links as input, grabs all corresponding pages from Wikipedia, and gives you a file of all Wikipedia entity mentions in those pages.

## Usage

Make sure [Python > 3][python] and [pip][pip] are running on your machine:

    python --version

Now clone Wikigrouth...

    git clone https://github.com/behas/wikigrouth.git

... and install the Wikigrouth library:

    cd wikigrouth
    pip install -r requirements.txt
    python setup.py install

Create an example seed file (or take some other textual file containg links in the form `<http://dbpedia.org/resource/Vienna>`):

    echo "<http://dbpedia.org/resource/Vienna>" > test.txt

...and run the corpus generation tool.

    wikigrouth test.txt

If you want to override already existing files use:

    wikigrouth -f test.txt

Your console will then tell you what's going on.


## Corpus Structure

Taking above example, the corpus will be generated in a folder `test` having the following internal file structure:

    |- index.csv (*corpus index file*)
    |- entities.csv (*extracted entities file*)
    |- html
      |- Vienna.html (*HTML page downloaded from Wikipedia*)
      |- ...
    |- text
      |- Vienna.txt (*Raw text file extracted from HTML page*)


### Corpus index file fields

For example above:

    doc_id,uri,html_file,text_file
    0,http://dbpedia.org/resource/Vienna,Vienna.html,Vienna.txt

CSV field semantics:

  * doc_id: autogenerated document id
  * uri: the seed uri
  * html_file: file name of HTML page retrieved from Wikipedia
  * text_file: file name of extracted text

### Extracted entities file fields

For example above:

    doc_id,offset,text,uri,in_seed
    0,21,German,http://dbpedia.org/resource/German_language,0
    0,99,Austria,http://dbpedia.org/resource/Austria,0
    0,128,states of Austria,http://dbpedia.org/resource/States_of_Austria,0
    0,246,metropolitan area,http://dbpedia.org/resource/Metropolitan_area,0
    0,312,its cultural,http://dbpedia.org/resource/Culture_of_Austria,0
    0,326,economic,http://dbpedia.org/resource/Economy_of_Austria,0
    0,340,political,http://dbpedia.org/resource/Politics_of_Austria,0
    0,368,7th-largest city,http://dbpedia.org/resource/Largest_cities_of_the_European_Union_by_population_within_city_limits,0
    0,425,European Union,http://dbpedia.org/resource/European_Union,0

CSV field semantics:

  * doc_id: document id (same as in corpus index file)
  * offset: character offset of entity surface form (token, term, text)
  * text: textual representation of entity
  * uri: unique entity identifier
  * in_seed: whether or not (0=no, 1=yes) entity is part of seed file 


## Notes

* At the moment Wikigrouth only supports seed files containing DBPedia URIs.


[wikilinks]: http://www.iesl.cs.umass.edu/data/wiki-links
[python]: https://www.python.org/
[pip]: https://pypi.python.org/pypi/pip
