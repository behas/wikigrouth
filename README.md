Wikigrouth - A Python tool for extracting entity mentions from a collection of Wikipedia documents.

# What is it good for?

Are you working on some coreference (or named entity) resolution task? Have you already reached the point of evaluating your solution? Then you probably know that you need some ground truth data set...and it is verly likely that you don't have it.

If you are looking for some large-scale and domain-independent data set, then you should look into [Wikilinks][wikilinks].

If you are working on some domain-specific task (e.g., sports, medicine, etc.), then Wikigrouth could be your solution. It takes a file containing Wikipedia or DBpedia links as input, grabs all corresponding pages from Wikipedia, and gives you a file of all Wikipedia entity mentions in those pages.

# Usage

Make sure [Python > 3][python] and [pip][pip] are running on your machine:

    python --version

Now clone Wikigrouth...

    git clone https://github.com/behas/wikigrouth.git

... and install the Wikigrouth library:

    cd wikigrouth
    python setup.py install

Create an example seed file (or take some other textual file containg links in the form `<http://dbpedia.org/resource/Vienna>`):

    echo "<http://dbpedia.org/resource/Vienna>" > test.txt

...and run the corpus generation tool.

    wikigrouth test.txt

If you want to override already existing files use:

    wikigrouth -f test.txt

Your console will then tell you what's going on.


# Corpus Structure


## Notes

* Supporting JSON-LD as export format would make life for Python/Ruby/etc people easier


[wikilinks]: http://www.iesl.cs.umass.edu/data/wiki-links
[python]: https://www.python.org/
[pip]: https://pypi.python.org/pypi/pip
