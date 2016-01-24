#!/usr/bin/env python
#http://stackoverflow.com/questions/5890659/beautifulsoup-and-searching-by-class
import os
import sys
import urllib2
import re
import collections
import time
from datetime import date

try:
    from bs4 import BeautifulSoup
    #import lxml.html
    import dateutil.parser
    from fake_useragent import UserAgent
    ua = UserAgent()
except ImportError:
    pass

VERSION = (0, 0, 2)
__version__ = '.'.join(map(str, VERSION))

DATE_PATTERN = re.compile('([0-9]+)\-([0-9]+)\-([0-9]+)')

def clean_name(v):
    return re.sub('[^a-zA-Z0-9_]+', '_', v.lower())

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
        
        # First row in the <thead>
        self._header = None
        
        # All rows in the <thead>
        self._header_list = []
        
        self._header_is_th = False
        self._header_extra_columns = 0
    
    @property
    def headers(self):
        found = False
        if not self._header:
            head_el = self._element.select('thead')
            rows = (head_el or self._element).select('tr')
            for row in rows:
                tmp_header = []
                q = row.select('th')
                if q:
                    found = True
                    self._header = [_.get_text() for _ in q]
                    self._header_is_th = True
                    self._header_extra_columns = sum(int(_.get('colspan', 1)) - 1 for _ in q)
                    self._header_list.append([_.get_text() for _ in q])
                    #break
                q = row.select('td')
                if q and not found:
                    self._header = [_.get_text() for _ in q]
                    self._header_is_th = False
                    break
        return [_.strip().replace('\n', ' ') for _ in self._header or []]
    
    @property
    def header_list(self):
        self.headers
        return self._header_list
    
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
        
    @property
    def fingerprints(self):
        return self.header_list
    
    def matches_fingerprint(self, other_fingerprint, select_matching=False):
        """
        Returns true if the given fingerprint matches at least one of the table's fingerprints.
        Returns false otherwise.
        """
        for fingerprint in self.fingerprints:
            matches = True
#             print 'f0:', fingerprint
#             print 'f1:', other_fingerprint
            for part0, part1 in zip(fingerprint, other_fingerprint):
#                 print 'parts:', part0, part1
                if isinstance(part1, basestring):
                    if part0.lower().strip() != part1.lower().strip():
                        matches = False
                        break
                elif type(part1).__name__ == 'SRE_Pattern':
                    if not part1.findall(part0):
                        matches = False
                        break
                else:
                    raise NotImplementedError, 'Unknown fingerprint part type: %s' % (part1,)
            if matches:
#                 print 'found!', other_fingerprint
                if select_matching:
                    self._header = fingerprint
                return True
        return False
    
    @classmethod
    def from_url(cls, url, fingerprint=None, raise_none=True, verbose=False):
        """
        url := The location to retrieve the raw HTML from
        fingerprint := A list of headers to use to filter tables.
            If given, only tables containing all these headers will be returned.
        """
        html = get(url=url)
        return cls.from_html(html, fingerprint, raise_none=raise_none, verbose=verbose)

    @classmethod
    def from_html(cls, html, fingerprint=None, raise_none=True, verbose=False):
        soup = BeautifulSoup(html, 'lxml')
        tables = _tables = map(cls, soup.select('table[class~=wikitable]'))
        
        if verbose:
            print 'tables:',len(tables)
            for _t in tables:
                print _t, 'headers:', _t.header_list
        
        if fingerprint:
            tables = [_t for _t in tables if _t.matches_fingerprint(fingerprint, select_matching=True)]
        
        if not tables and raise_none:
            raise Exception, 'No tables found matching fingerprint: %s\n\nOnly found:\n    %s' % (
                fingerprint,
                '\n    '.join([str(_t.fingerprint) for _t in _tables])
            )
        
        return tables
        