#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generic downloader tentacle"""
WClassName = 'GenericTentacle'

import multiprocessing

import logging
logger = logging.getLogger(__name__)

class GenericTentacle(multiprocessing.Process):
    def __init__(self, in_queue, out_queue, conf_obj):

        multiprocessing.Process.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def supports(self, thing):
        """
        Returns True if the url is supported by this tentacle otherwise False
        """
        if thing.url.scheme not in ('http','https'):
            logger.debug("%s does not suppport '%s' scheme" % (WClassName, thing.url.scheme))
            return False
        return True

    def run(self):
        proc_name = self.name
        while True:
            next_task = self.in_queue.get()
            jid, thing = next_task

            #SAVE FILE IN MEDIA DIRECTORY

            if thing.save_file(self.conf_obj.get_dir(thing.mimetype.mimetype)):
                message = "ALL OK MASTER %s downloaded as %s" % (thing.url.href(), thing.filename)
            else:
                message = "I WAS NOT ABLE TO DO STUFF MASTER"
            self.out_queue.put((jid, message))
            
            #print "FILE IS here", thing
            #ANSWER BACK TO USER
            message = "ALL OK MASTER"
            self.out_queue.put((jid, message))

