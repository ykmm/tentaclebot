#!/usr/bin/env python
# -*- coding: utf-8 -*-
# by Yann Melikoff

import sys
import re
import pycurl
#pycurl.COOKIESESSION = 96
import urllib
import json
sys.path.insert(1,'./')
from BeautifulSoup import BeautifulSoup
import tempfile
import logging
from base64 import b64encode
from StringIO import StringIO

CT_XWWW = 'x-www'
CT_XML = 'text/xml'
CT_JSON = 'application/json'
CT_COLL_JSON = 'application/vnd.collection+json'
CTYPES = {CT_XWWW: 'Content-Type: application/x-www-form-urlencoded',
          CT_XML: 'Contenty-Type: text/xml',
          CT_JSON: 'Content-Type: application/json', 
          CT_COLL_JSON: 'Content-Type: application/vnd.collection+json'}

HTTP_Badrequest = 400
HTTP_Unathorized = 401
HTTP_Forbidden = 403
HTTP_Locked = 423
HTTP_Created = 201
HTTP_OK = 200

class DocExtractor:

    def __init__(self, debug=False):
        self.c = pycurl.Curl()
        self.debug = debug
        self.reset()
        self.buffer = ''
        self.last_buffer = ''
        self.headers = dict()
        self.last_headers = dict()
        self._http_request_headers=list()
        self.lastURL = ''
        self.lastPARAMS = ''

    def reset(self):
        self.c.reset()
        #self.buffer = ''
        #self.headers = list()
        self.c.setopt(pycurl.FOLLOWLOCATION,0)
        self.c.setopt(pycurl.COOKIEJAR,'cookies.txt')
        self.c.setopt(pycurl.COOKIEFILE,'cookies.txt')
        #self.c.setopt(pycurl.COOKIESESSION, True)
        self.c.setopt(pycurl.USERAGENT,'DocExtractorMM')
        self.c.setopt(pycurl.WRITEFUNCTION, self.fill_buffer)
        self.c.setopt(pycurl.HEADERFUNCTION, self.fill_headers)
        self.c.setopt(pycurl.SSL_VERIFYPEER, False)
        self.c.setopt(pycurl.SSL_VERIFYHOST, False)
        if self.debug:
            self.c.setopt(pycurl.HEADER,0) #Include headers in output
            self.c.setopt(pycurl.VERBOSE,1) #Connection info in stderr


    def GET(self, url, params=None, auth = None):
        return self.get_url(url, params, auth = auth)

    def PUT(self, url, params=None, auth = None, content_type = CT_XWWW):
        return self.get_url(url, params, method='PUT', auth = auth, content_type = content_type)

    def POST(self, url, params=None, auth = None, content_type = CT_XWWW):
        return self.get_url(url, params, method='POST', auth = auth, content_type = content_type)

    def DELETE(self, url, params=None, auth = None):
        return self.get_url(url, params, method='DELETE', auth = auth)

    def get_url(self, url, params=None, method='GET', auth=None, content_type=CT_XWWW):
        self.reset()
        """Retrieve page url
        params is a optional dictionary of (key,value)s (value can be a list and it will be encoded properly)
        method can be 'GET' (default) or 'POST'
        auth if set must be a tuple (username, password)
        stores resulting page in buffer
        """

        self.c.setopt(pycurl.URL,url.encode('ascii'))
        paramstring = None
        param_tuples = list()
        if content_type in CT_XWWW:
            if params is not None:
                for k,v in params.items():
                    if isinstance(v,(int,long)):
                        #Convertiamo tutto in utf8 perchè urllib non ce la fa da solo
                        param_tuples.append((k,str(v).encode('utf-8')))
                    elif isinstance(v,list):
                        for elem in v:
                            param_tuples.append((k,str(elem).encode('utf-8')))
                    else:
                        param_tuples.append((k,v.encode('utf-8')))

                paramstring = urllib.urlencode(param_tuples)

        elif content_type == CT_JSON:
            if params is not None:
                paramstring=json.dumps(params)
            else:
                paramstring='{}'

        elif content_type == CT_XML:
            if params is not None:
                paramstring = params
        elif content_type == CT_COLL_JSON:
            if params is not None:
                paramstring = params

        if method == 'GET':
            if paramstring:
                self.c.setopt(self.c.URL,url + '?' + paramstring);

        if method == 'POST':
            self.c.setopt(pycurl.POST, True)
            #self.c.setopt(pycurl.CUSTOMREQUEST, 'POST')
            if not paramstring:
                paramstring = ''
            self.c.setopt(pycurl.POSTFIELDS, paramstring)
            self.add_http_request_header(CTYPES[content_type])

        if method == 'PUT':
            self.c.setopt(pycurl.PUT, True)
            if not paramstring:
                paramstring = ''
            paramIO = StringIO(paramstring)
            self.c.setopt(pycurl.READFUNCTION, paramIO.read)
            self.c.setopt(pycurl.INFILESIZE, len(paramstring))
            #self.c.setopt(pycurl.HTTPHEADER, [CTYPES[content_type]])
            self.add_http_request_header(CTYPES[content_type])

        if method == 'DELETE':
            self.c.setopt(pycurl.CUSTOMREQUEST, 'DELETE')

        if auth:
            self.c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
            self.c.setopt(pycurl.USERPWD, '%s:%s' % (auth[0].encode('utf8'),auth[1].encode('utf8')))

        self.set_http_request_headers()
        self.c.perform()
        self.lastURL = url
        self.lastPARAMS = paramstring
        self.write_cookie_jar()
        return self.c.getinfo(pycurl.RESPONSE_CODE), self.pop_buffer()

    def add_http_request_header(self, header):
        if header not in self._http_request_headers:
            self._http_request_headers.append(header)

    def reset_http_request_headers(self):
        self._http_request_headers = list()

    def set_http_request_headers(self):
        self.c.setopt(pycurl.HTTPHEADER, self._http_request_headers)

    def add_cookies(self, cookielist, write_to_jar=True):
        """
        cookielist: array of Netscape/Set-Cookie cookie strings
        write_to_jar: write to cookiejar, default True
        """
        for cookie in cookielist:
            self.c.setopt(pycurl.COOKIELIST, cookie)
        if write_to_jar:
            self.write_cookie_jar()

    def del_cookies(self, cookienames, write_to_jar=True):
        """
        cookielist: array of cookie names to be deleted for all urls
        write_to_jar: write to cookiejar, default True
        """
        newlist = list()
        cookielist = self.get_cookie_list()
        for cookie in cookielist:
            s = cookie.split('\t')
            if s[5] not in cookienames:
                newlist.append(cookie)

        self.reset_cookie_jar()
        self.add_cookies(newlist, write_to_jar)

    def write_cookie_jar(self):
        self.c.setopt(pycurl.COOKIELIST, 'FLUSH')

    def reset_cookie_jar(self):
        self.c.setopt(pycurl.COOKIELIST, 'ALL')

    def get_cookie_list(self):
        return self.c.getinfo(pycurl.INFO_COOKIELIST)

    def get_form_fields(self, htmldata, form_id=None, form_name=None):
        """Returns a dictionary populated with fields:values from all
        input/select found in the form in htmldata with id form_id
        """
        formattrs = dict()
        search_params = dict()

        searchsoup = BeautifulSoup(htmldata)

        if form_id is None and form_name is None:
            input_fields = searchsoup.findAll('input')
            select_fields = searchsoup.findAll('select')
        else:
            if form_id is not None:
                formattrs['id'] = form_id

            if form_name is not None:
                formattrs['name'] = form_name

            try:
                formsoup = searchsoup.findAll('form',attrs=formattrs)[0]
            except IndexError:
                return None

            input_fields = formsoup.findAll('input')
            select_fields = formsoup.findAll('select')
        """
        if form_id is not None:
            try:
                input_fields = searchsoup.findAll('form',attrs={'id':form_id})[0].findAll('input')
            except IndexError:
                return None
            try:
                select_fields = searchsoup.findAll('form',attrs={'id':form_id})[0].findAll('select')
            except IndexError:
                return None
        elif form_name is not None:
            try:
                input_fields = searchsoup.findAll('form',attrs={'name':form_name})[0].findAll('input')
            except IndexError:
                return None
            try:
                select_fields = searchsoup.findAll('form',attrs={'name':form_name})[0].findAll('select')
            except IndexError:
                return None
        else:
            input_fields = searchsoup.findAll('input')
            select_fields = searchsoup.findAll('select')
        """
        for field in input_fields:
            if field['type'] == 'radio':
                if field.has_key('checked') and field.has_key('value'):
                    if field.has_key('name'):
                        search_params[field['name']] = field['value']
                    if field.has_key('property'):
                        search_params[field['property']] = field['value']
            elif field['type'] == 'checkbox':
                if field.has_key('checked'):
                    search_params[field['name']] = field['value']

            else:
                if field.has_key('name'):
                    if field.has_key('value'):
                        search_params[field['name']] = field['value']
                    else:
                        search_params[field['name']] = ''


        for select in select_fields:
            options = select.findAll('option')
            try:
                search_params[select.get('name')] = options[0].get('value') #gets first option
            except KeyError:
                search_params[select.get('name')] = ''

        return search_params

    def fill_buffer(self,buf):
        self.buffer = self.buffer + buf

    def pop_buffer(self):
        t = self.buffer
        self.last_buffer = self.buffer
        self.buffer = ''
        return t

    def fill_headers(self,buf):
        if re.search(r':',buf):
            k = buf[0:buf.index(':')]
            v = buf[buf.index(':')+1:]
            v = re.sub('^ *', '', v)
            v = re.sub('[\r\n]', '', v)
            self.headers[k] = v

    def pop_headers(self):
        t = dict(self.headers) #copio il dizionario
        self.last_headers = self.headers
        self.headers = dict()
        return t

    def save_temp_file(self, filedata):
        """Creates a temporary file containing filedata
        returns the temporary file name
        """
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(filedata)
        tmp_file.close()
        return tmp_file.name

    def save_file(self, filedata, filename):
        """Stores the file containing filedata in it
        returns the file name
        """

        tmp_file = open(filename,'wb')
        tmp_file.write(filedata)
        tmp_file.close()
        return tmp_file.name

if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    de = DocExtractor()
    de.get_url('http://www.example.com')
    #print de.pop_buffer()
    print "HEADERS", de.pop_headers()

    de.get_url('http://www.example.com')
    #print de.pop_buffer()
    print "HEADERS", de.pop_headers()
