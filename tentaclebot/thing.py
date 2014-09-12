#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)
import os, errno
import shutil
import tempfile
from docextractor.docextractor import DocExtractor
from httprep.url import Url

import magic

class MimeType(object):

    def __init__(self, mimetype):
        self.mimetype = mimetype
        self.mtype, self.msubtype = self.mimetype.split("/")

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
    filename = None

    def __init__(self, url):
        self.url = Url(url)

    def dereference_url(self):
        if not self._content_aquired:
            logger.debug("Downloading...")
            self._content_aquired = True
            DE = DocExtractor()
            try:
                self._http_code, self._http_data = DE.get_url(self.url.href())
                self._http_headers = DE.pop_headers()
                _temp_file = tempfile.NamedTemporaryFile(delete=False)
                _temp_file.write(self._http_data)
                _temp_file.close()
                self.filename = _temp_file.name
            except:
                raise

    def save_file(self, path):
        """Moves the temporary file in the folder specified by `path`"""
        try:
            filename = os.path.basename(self.url.path)
            if len(filename)==0:
                filename = os.path.basename(self.filename)
                try:
                    os.makedirs(path)
                except OSError, e:
                    if not e == errno.EEXIST:
                        raise
            #Move file in position
            shutil.move(self.temp_file, path+filename)
        except:
            raise
        else:
            self.filename = path+filename
            logger.debug("File saved as %s" % (self.filename))
            return True

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
        return self.filename

    @property
    def mimetype(self):
        self.dereference_url()
        return MimeType(magic.from_file(self.temp_file, mime=True))

