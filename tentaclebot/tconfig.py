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
    media_dir = "/tmp/"
    torrent_watch = "/tmp/"

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
            #Check directory existence
            if not os.path.isdir(self.media_dir):
                raise ConfigurationException, "media directory %s does not exist" % self.media_dir
            if not os.path.isdir(self.torrent_watch):
                raise ConfigurationException, "torrent watch directory %s does not exist" % self.media_dir


    def load_conf_from_file(self, filename):
        try:
            f = open(filename)
        except IOError:
            self.local_conf = False
        else:
            self.local_conf = True
            conf_data = yaml.safe_load(f)
            f.close()
            self.jid = conf_data['jid']
            self.password = conf_data['password']
            self.allowed_users = conf_data['allowed_users']
            self.media_dir = conf_data['media_dir']
            self.torrent_watch = conf_data['torrent_watch']
            self.video_write_metadata = conf_data['video']['write_metadata']

