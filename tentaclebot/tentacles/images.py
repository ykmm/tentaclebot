#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Image downloader tentacle"""
WClassName = 'ImageTentacle'

import multiprocessing
import os

import logging
logger = logging.getLogger(__name__)

class ImageTentacle(multiprocessing.Process):
    def __init__(self, in_queue, out_queue, conf_obj):
        multiprocessing.Process.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.save_dir = conf_obj.media_dir

    def supports(self, thing):
        #Verifica se è un link magnet e facci qualcosa
        if thing.url.scheme in ('http','https'):
            if thing.mimetype.mtype == 'image':
                return True
            else:
                return False
        else:
            logger.debug("%s does not suppport '%s' scheme" % (WClassName, thing.url.scheme))
            return False

    def run(self):
        proc_name = self.name

        while True:
            next_task = self.in_queue.get()

            jid, thing = next_task

            if thing.url.scheme in ('http','https'):
                logger.info(thing.http_headers)
                if thing.save_file(self.save_dir):
                    message = "ALL OK MASTER %s downloaded as %s" % (thing.url.href(), thing.filename)
                else:
                    message = "I WAS NOT ABLE TO DO STUFF MASTER"

                self.out_queue.put((jid, message))
            if thing.url.scheme in ('magnet'):
                message = "I DON'T KNOW HOW TO DEAL WITH MAGNET LINKS YET, TEACH ME MASTER, PLEASE!"
                self.out_queue.put((jid, message))
