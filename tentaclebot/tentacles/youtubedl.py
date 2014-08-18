#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Video streaming downloader tentacle (uses youtube-dl)"""
WClassName = 'YoutubeTentacle'

import multiprocessing

import youtube_dl
_extractors = youtube_dl.extractor.gen_extractors()
#LOG = multiprocessing.get_logger()
logger = multiprocessing.log_to_stderr()
logger.setLevel(multiprocessing.SUBDEBUG)

class YoutubeTentacle(multiprocessing.Process):
    def __init__(self, in_queue, out_queue, save_dir = './'):
        multiprocessing.Process.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

        self.ydl = youtube_dl.YoutubeDL({'outtmpl': save_dir + u'%(title)s-%(id)s.%(ext)s'})

        # Add all the available extractors
        self.ydl.add_default_info_extractors()

    def supports(self, thing):
        """
        Returns True if the url is supported by this tentacle otherwise False
        """
        if thing.url.scheme not in ('http','https'):
            return False
        for ie in sorted(_extractors, key=lambda ie: ie.IE_NAME.lower()):
            if ie._WORKING and ie.suitable(thing.url.href()):
                if ie.IE_NAME == 'generic':
                    continue
                logger.info('SUPORTO? SI')
                return True
        logger.info('SUPORTO? NO')
        return False

    def run(self):
        proc_name = self.name
        while True:
            next_task = self.in_queue.get()
            jid, thing = next_task

            try:
                result = self.ydl.extract_info(thing.url.href(), download=True)
            except youtube_dl.DownloadError,e :
                print e
            else:
                if 'entries' in result:
                    # Can be a playlist or a list of videos
                    video = result['entries'][0]
                else:
                    # Just a video
                    video = result
                title = video['title']
                logger.info('DICO COSE FINITE')
                message = "'%s' HAS BEEN DOWNLOADED MASTER" % title
                self.out_queue.put((jid, message))
                #import json
                #print json.dumps(video,indent=4)
                #video_url = video['url']
