#!/usr/bin/env python
#http://stackoverflow.com/questions/5890659/beautifulsoup-and-searching-by-class
import os
import sys
import urllib2
import re
import collections
import time
from datetime import date

from bs4 import BeautifulSoup
#import lxml.html

import dateutil.parser

from fake_useragent import UserAgent
ua = UserAgent()

VERSION = (0, 0, 1)
__version__ = '.'.join(map(str, VERSION))

DATE_PATTERN = re.compile('([0-9]+)\-([0-9]+)\-([0-9]+)')

def clean_name(v):
    return re.sub('[^a-zA-Z0-9_]+', '_', v)

def unquote(s):
    s = s.strip()
    if s and s[0] in ('"', "'") and s[-1] in ('"', "'"):
        s = s[1:-1]
    return s

def to_num(v):
    if not isinstance(v, basestring):
        return v
    try:
        return int(v.replace(',', ''))
    except ValueError:
        pass
    try:
        return flat(v.replace(',', ''))
    except ValueError:
        pass

def iter_all_visible_content(el):
    for child in el.children:
        if hasattr(child, 'attrs'):
            style = child.attrs.get('style', '')
            if 'display:none' in style:
                continue
                
        if hasattr(child, 'children'):
            for _child in iter_all_visible_content(child):
                yield _child
        else:
            yield child
            
def get(
    url,
    user_agent=None,
    verbose=False,
    max_retries=10,
    initial_delay_seconds=2,
    retry_delay_multiplier=2,
    ignore_404=False,
    max_delay_seconds=60):
    """
    Retreives the content of a URL, applying a customizable user-agent and
    intelligentally waiting when network errors are encountered.
    """
    _user_agent = user_agent
    for retry in xrange(max_retries):
        try:
            if _user_agent is None:
                user_agent = ua.random
            if verbose:
                print url
            request = urllib2.Request(
                url=url,
                headers={'User-agent': user_agent})
            response = urllib2.urlopen(request)
            break
        except urllib2.HTTPError, e:
            if 'not found' in str(e).lower() and not ignore_404:
                raise
            if verbose:
                print>>sys.stderr, 'scrapper.get.error: %s' % (e,)
            if retry == max_retries-1:
                raise
            # Wait a short while, in case the error is due to a temporary
            # networking problem.
            time.sleep(min(
                max_delay_seconds,
                initial_delay_seconds + retry*retry_delay_multiplier))
    html = response.read()
    return html

class Table(object):
    
    def __init__(self, element):
        self._element = element
        self._header = None
        self._header_is_th = False
        self._header_extra_columns = 0
    
    @property
    def headers(self):
        if not self._header:
            rows = self._element.select('tr')
            for row in rows:
                q = row.select('th')
                if q:
                    self._header = [_.get_text() for _ in q]
                    self._header_is_th = True
                    self._header_extra_columns = sum(int(_.get('colspan', 1)) - 1 for _ in q)
                    break
                q = row.select('td')
                if q:
                    self._header = [_.get_text() for _ in q]
                    self._header_is_th = False
                    break
        return [_.strip().replace('\n', ' ') for _ in self._header or []]
    
    @property
    def clean_headers(self):
        return [_.strip().lower().replace('\n', ' ') for _ in self.headers]
    
    def get_rows(self, raw=False, as_dict=True):
        headers = list(self.headers)
        rows = self._element.select('tr')
        for row in rows:
            tds = row.select('td')
            if not tds:
                continue
            if not raw:
                clean_row = []
                for name, td in zip(headers, tds):
                    clean_row.append(self._clean_td(td, name=name))
                tds = clean_row
            if as_dict:
                tds = dict(zip(headers, tds))
            yield tds
    
    @property
    def rows(self):
        for _ in self.get_rows():
            yield _
    
    def __iter__(self):
        for _ in self.get_rows():
            yield _
    
    @property
    def row_count(self):
        return len(list(self.get_rows()))
    
    def _clean_td(self, td, name=None):
        """
        Converts a raw messy TD node and converts it to pure data.
        """
        
        # Get text at just the current node.
#         text = td.findAll(text=True, recursive=False)
#         if text:
#             return ' '.join(text)
#             
#         # Otherwise, get text from all children, in cases where the TD node contains spans/etc.
#         # Note, this is potentially messier and will clump data together, causing noise.
#         text = td.get_text()
        
        text = iter_all_visible_content(td)
        text = ' '.join(text)
        text = text.strip()
        
        if name:
            func_name = 'clean_%s' % clean_name(name.lower())
            if hasattr(self, func_name):
                text = getattr(self, func_name)(text)
            elif name.lower() == 'date':
                text = self.clean_date(text)
        
        return text
    
    def clean_date(self, v):
        date_val = None
        try:
            date_val = dateutil.parser.parse(v)
        except TypeError:
            print>>sys.stderr, 'Unknown data:', v
            pass
        except ValueError:
            print>>sys.stderr, 'Unknown data:', v
            pass
        if date_val is None:
            matches = re.findall(DATE_PATTERN, v)
            if matches:
                date_val = date(*map(int, matches[0]))
        return date_val
    
    @property
    def fingerprint(self):
        return set([_.strip().lower() for _ in self.headers])
    
    @classmethod
    def from_url(cls, url, fingerprint=None):
        """
        url := The location to retrieve the raw HTML from
        fingerprint := A list of headers to use to filter tables.
            If given, only tables containing all these headers will be returned.
        """
        html = get(url=url)
        return cls.from_html(html, fingerprint)

    @classmethod
    def from_html(cls, html, fingerprint=None):
        soup = BeautifulSoup(html, 'lxml')
        tables = map(cls, soup.select('table[class~=wikitable]'))
        
        if fingerprint:
            fingerprint = set([_.strip().lower() for _ in fingerprint])
            tables = [_t for _t in tables if _t.fingerprint.issuperset(fingerprint)]
        
        return tables
        