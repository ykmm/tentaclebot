#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import filetype

def supported(url):
    _ft = filetype.filtype()
    for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
        if ie._WORKING and ie.suitable(url):
            if ie.IE_NAME == 'generic':
                continue
            return True
    return False

class Worker(multiprocessing.Process):
    def __init__(self, in_queue, out_queue):
        multiprocessing.Process.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        proc_name = self.name
        while True:
            next_task = self.in_queue.get()
            print proc_name, "WORKER WORKS WORK!", next_task

            videourl = next_task
            # download=False because we just want to extract the info
            try:
                result = self.ydl.extract_info(videourl, download=False)
            except youtube_dl.DownloadError,e :
                print e
            else:
                if 'entries' in result:
                    # Can be a playlist or a list of videos
                    video = result['entries'][0]
                else:
                    # Just a video
                    video = result
                self.out_queue.put(video)
                print(video)
                video_url = video['url']
                print(video_url)
