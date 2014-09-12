#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    TentacleBOT: The Offlineator!
"""

import logging
import yaml
import os

class ConfigurationException(Exception):
    pass

class TConfig(object):
    """
    A simple class to represent a configuration object
    """
    jid = None
    password = None
    allowed_users = list()

    main_conf = False
    local_conf = False

    def __init__(self, conf_file_dir='./'):

        try:
            self.load_conf_from_file(conf_file_dir + 'tconfig.yaml')
            self.main_conf = True
        except IOError:
            self.main_conf = False


        try:
            self.load_conf_from_file(conf_file_dir + 'tconfig-local.yaml')
            self.local_conf = True
        except IOError:
            self.local_conf = False

        if not self.main_conf and not self.local_conf:
            raise ConfigurationException, "tconfig.yaml or tconfig-local.yaml not found"
        else:
            #do something else
            pass

    def load_conf_from_file(self, filename):
        try:
            f = open(filename)
        except IOError:
            self.local_conf = False
        else:
            self.local_conf = True
            self.conf = yaml.safe_load(f)
            f.close()
            self.jid = self.conf['jid']
            self.password = self.conf['password']
            self.allowed_users = self.conf['allowed_users']
            self.video_write_metadata = self.conf['video']['write_metadata']
            
            self.storage = self.conf['storage']
            
    def get_dir(self, mimetype):
        """Given a `mimetype` it returns the directory where it need to be
        saved based on the storage rules in the configuration file
        
        """
        b = self.storage['basedir']
        r = self.storage['mimerules']
        #First check for full mimetype
        if mimetype in r:
            return "%s%s" % (b, r[mimetype])
        _type, _ = mimetype.split('/')
        #Then check only for type
        if _type in r:
            return "%s%s" % (b, r[_type])
        #Return main download dir
        return b
