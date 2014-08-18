#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
from docextractor.docextractor import DocExtractor, pycurl
from httprep.url import Url

class Thing(object):
    """Representes something to be downloaded

    This object will be passed to each plugin in turn to see if it is
    supported.

    Some plugins just need to evaluate the url, others need to have it
    dereferenced, to avoid unnecessary redownloads, we use a class property
    to cache the dereferenced url for all subsequent checks

    """

    url = None
    _content_aquired = False
    _http_code = None
    _http_data = None
    _http_headers = None
    _temp_file_name = None

    def __init__(self, url):
        self.url = Url(url)

    def dereference_url(self):
        if not self._content_aquired:
            self._content_aquired = True
            DE = DocExtractor()
            try:
                self._http_code, self._http_data = DE.get_url(self.url.href())
                self._http_headers = DE.pop_headers()
                _temp_file = tempfile.NamedTemporaryFile(delete=False)
                _temp_file.write(self._http_data)
                _temp_file.close()
                self._temp_file_name = _temp_file.name
            except:
                raise

    #TODO, add __del__ method to delete temporary file if created

    @property
    def http_code(self):
        self.dereference_url()
        return self._http_code

    @property
    def http_data(self):
        self.dereference_url()
        return self._http_data

    @property
    def http_headers(self):
        self.dereference_url()
        return self._http_headers

    @property
    def temp_file(self):
        self.dereference_url()
        return self._temp_file_name