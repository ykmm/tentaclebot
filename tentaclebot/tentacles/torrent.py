#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Torrent and magnet downloader tentacle"""
WClassName = 'TorrentTentacle'

import multiprocessing
import filetype
import os

logger = multiprocessing.log_to_stderr()
logger.setLevel(multiprocessing.SUBDEBUG)

class TorrentTentacle(multiprocessing.Process):
    def __init__(self, in_queue, out_queue, save_dir = './'):
        multiprocessing.Process.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.save_dir = save_dir

    def supports(self, thing):
        #Verifica se è un link magnet e facci qualcosa
        if thing.url.scheme in ('http','https'):
            _ft = filetype.filetype(thing.temp_file)
            if _ft == 'BitTorrent file':
                return True
            else:
                return False
        elif thing.url.scheme == 'magnet':
            return True
        else:
            return False

    def run(self):
        proc_name = self.name

        while True:
            next_task = self.in_queue.get()

            jid, thing = next_task

            #SAVE FILE IN MEDIA DIRECTORY
            if thing.url.scheme in ('http','https'):
                #ANSWER BACK TO USER
                logger.info("%s answer fokke" % proc_name)
    
                message = "ALL OK MASTER %s %s" % (thing.url.href(), thing.temp_file)
    
                logger.info(thing.http_headers)
                filename = os.path.basename(thing.url.path)
                if len(filename)==0:
                    filename = os.path.basename(thing.temp_file)
                os.rename(thing.temp_file, self.save_dir+filename)
                self.out_queue.put((jid, message))
            if thing.url.scheme in ('magnet'):
                message = "I DON'T KNOW HOW TO DEAL WITH MAGNET LINKS YET, TEACH ME MASTER, PLEASE!"
                self.out_queue.put((jid, message))
