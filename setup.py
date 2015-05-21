from __future__ import print_function
from setuptools import setup
# from setuptools.command.test import test as TestCommand
import io
# import sys

import wikigrouth


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


# long_description = read('README.rst')

# class PyTest(TestCommand):
#     def finalize_options(self):
#         TestCommand.finalize_options(self)
#         self.test_args = []
#         self.test_suite = True

#     def run_tests(self):
#         import pytest
#         errcode = pytest.main(self.test_args)
#         sys.exit(errcode)


setup(
    # Basic info
    name='wikigrouth',
    version=wikigrouth.__version__,
    url='https://github.com/behas/wikigrouth.git',

    # Author
    author='Bernhard Haslhofer',
    author_email='bernhard.haslhofer@ait.ac.at',

    # Description
    description="""A Python tool for creating coreference resolution
                ground truths from Wikipedia.""",

    # long_description=long_description,

    # Package information
    packages=['wikigrouth'],
    scripts=['scripts/wikigrouth'],
    platforms='any',
    install_requires=['requests', 'beautifulsoup4'],
    classifiers=[
         'Development Status :: 4 - Beta',
         'Environment :: Console',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: MIT License',
         'Operating System :: OS Independent',
         'Programming Language :: Python :: 3',
         'Topic :: Software Development :: Libraries',
    ],

    # Testing
    # test_suite='tests',
    # tests_require=['pytest'],
    # cmdclass={'test': PyTest},
    # extras_require={
    #     'testing': ['pytest'],
    # },

    # Legal info
    license='MIT License',
)
