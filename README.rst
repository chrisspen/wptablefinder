=============================================================================
WPTableFinder - Finds and extracts tables from Wikipedia
=============================================================================

Overview
--------

Finds tables in the raw HTML of a Wikipedia page and converts them
to a clean list-of-dictionaries, suitable for easy processing in Python.

Note, this is a convenience tool to help one-off processing of specific
Wikipedia pages, where downloading an entire Wikipedia snapshot would be
impractical. It's inefficient and will not scale well for bulk use.
If you need to do bulk processing of a large number of pages in Wikipedia, please download
and process a `Wikipedia snapshot <https://en.wikipedia.org/wiki/Wikipedia:Database_download>`_
.

Installation
------------

Install using pip via:

::

    sudo pip install wptablefinder
    
Usage
-----

    >>> from wptablefinder import Table
    >>> table = Table.from_url('https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population')[0]
    >>> print table.headers
    [u'Rank', u'Country (or dependent territory)', u'Population', u'Date', u'% of world population', u'Source']
    >>> for row in table:
    ...  print row
    {u'% of world population': u'18.9%', u'Rank': u'1', u'Source': u'Official population clock', u'Country (or dependent territory)': u'China [ Note 2 ]', u'Date': datetime.datetime(2015, 8, 15, 0, 0), u'Population': u'1,371,520,000'}
    ...
