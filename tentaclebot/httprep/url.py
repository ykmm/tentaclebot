#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urlparse
import urllib

class Url(object):
    """Class for representing an url

    >>> from url import Url
    >>> url = Url('http://example.com/test?k1=va&k1=vb&k2=v2')
    >>> print url
    Url(url='http://example.com/test?k1=va&k1=vb&k2=v2', urlparams=[])
    >>> print url.href()
    http://example.com/test?k2=v2&k1=va&k1=vb

    >>> url = Url('http://example.com/test', [('k1', 'va'), ('k1', 'vb'), ('k2', 'v2')])
    >>> print url
    Url(url='http://example.com/test', urlparams=[('k1', 'va'), ('k1', 'vb'), ('k2', 'v2')])
    >>> print url.href()
    http://example.com/test?k2=v2&k1=va&k1=vb

    >>> url = Url('http://example.com/test?k1=va&k1=vb&k2=vc', [('k2', 'vd'), ('k3', 'v3')])
    >>> print url
    Url(url='http://example.com/test?k1=va&k1=vb&k2=vc', urlparams=[('k2', 'vd'), ('k3', 'v3')])
    >>> print url.href()
    http://example.com/test?k3=v3&k2=vc&k2=vd&k1=va&k1=vb

    >>> url = Url('http://example.com/test')
    >>> url.add_query('k1', ['va', 'vb', 'vc'])
    >>> url.add_query('k2', 'v2')
    >>> print url
    Url(url='http://example.com/test', urlparams=[])
    >>> print url.href()
    http://example.com/test?k2=v2&k1=va&k1=vb&k1=vc

    """

    def __init__(self, url='', urlparams=list()):
        """url must be a string urlparams must be a list of (key,value) tuples value can be a list"""
        if not isinstance(url, (str, unicode)):
            raise ValueError, "url must be a string"
        self._url = url
        self._urlparams = urlparams

        self._scheme, self._netloc, self._path, \
            self._params, self._query, self._fragment = \
            urlparse.urlparse(url)

        #extract query string parameters in dict
        self._query_dict = urlparse.parse_qs(self._query)

        #Convertiamo tutto in utf8 perchè urllib non ce la fa da solo
        for k, v in urlparams:
            self.add_query(k, v)

    def _encode_utf8(self, int_str_list):
        if isinstance(int_str_list, (int, long)):
            return str(int_str_list).encode('utf-8')
        elif isinstance(int_str_list, (str, unicode)):
            return int_str_list.encode('utf-8')
        elif isinstance(int_str_list, list):
            return [str(x).encode('utf-8') for x in int_str_list]

    def __repr__(self):
        return "Url(url=%r, urlparams=%r)" % (self._url, self._urlparams)

    def add_query(self, name, value):
        """Add a query param by name and value"""
        if name not in self._query_dict:
            if isinstance(value, list):
                self._query_dict[name] = self._encode_utf8(value)
            else:
                self._query_dict[name] = [self._encode_utf8(value)]
        else:
            if isinstance(value, list):
                self._query_dict[name].extend(self._encode_utf8(value))
            else:
                self._query_dict[name].append(self._encode_utf8(value))

    def get_param(self, name):
        """Get param value by name"""
        return self._query_dict[name]

    def get_params(self):
        """Get all query parameters"""
        return self._query_dict

    def href(self, scheme=None, netloc=None, path=None,
                  path_append=True, params=None, query_dict=None,
                  query_replace=False, fragment=None):
        """Returns a string representation of the url

        scheme,netloc,path,params,query,fragment if passed are used instead
        of the internal representation to build the string, the values are
        not retained

        query_dict is a dictionary of url parameters, the values can be lists

        if query_replace is True query_dict replaces the internal query_dict
        if path_append is False path replaces the internal path
        """
        _scheme = scheme or self._scheme
        _netloc = netloc or self._netloc

        if path is None:
            _path = self._path
        else:
            if path_append:
                _path = self._path + path
            else:
                _path = path

        _params = params or self._params

        if query_dict is None:
            _query_dict = self._query_dict
        else:
            if query_replace:
                _query_dict = query_dict
            else:
                _query_dict = self._query_dict.copy()
                _query_dict.update(query_dict)


        _fragment = fragment or self._fragment

        return urlparse.ParseResult(_scheme,
                                    _netloc,
                                    _path,
                                    _params,
                                    urllib.urlencode(_query_dict, doseq=True),
                                    _fragment).geturl()
    @property
    def scheme(self):
        return self._scheme

    @property
    def path(self):
        return self._path
    
if __name__ == '__main__':
    url = Url('http://example.com/test?k1=va&k1=vb&k2=v2')
    print url
    print url.href()
    print url.href(path='/vangone/caramella')
    print url.href(scheme='https', query_dict={'pippo':['pluto']})
    url = Url('http://example.com/test', [('k1', 'va'), ('k1', 'vb'), ('k2', 'v2')])
    print url
    print url.href()
    url = Url('http://example.com/test?k1=va&k1=vb&k2=vc', [('k2', 'vd'), ('k3', 'v3')])
    print url
    print url.href()
    url = Url('http://example.com/test')
    url.add_query('k1', ['va', 'vb', 'vc'])
    url.add_query('k2', 'v2')
    print url
    print url.href()
