#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    TentacleBOT: The Offlineator!
"""

import sys
import logging, logging.config
import getpass
from optparse import OptionParser
import sleekxmpp
import yaml

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

import random
CONFIRM = ('YES MASTER', 'I UNDERSTAND MASTER', 'IMMEDIATELY MASTER')
SUCCESS = ('IT IS READY MASTER', 'DONE MASTER', 'COMPLETED MASTER')
UNRECOGNIZED = ('I DO NOT UNDERSTAND MASTER', 'I DO NOT KNOW WHAT TO DO MASTER')
ERROR = ('SORRY MASTER', 'I CAN\'T DO THAT MASTER', 'IT IS NOT POSSIBLE MASTER', 'FORGIVE ME MASTER')

import multiprocessing

import tentacles

from thing import Thing

class TentacleBot(sleekxmpp.ClientXMPP):
    """
    A simple SleekXMPP bot that will echo messages it
    receives, along with a short thank you message.
    """

    def __init__(self, config):
        self.config = config
        sleekxmpp.ClientXMPP.__init__(self, config.jid, config.password)

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self.message)

        #OUT queue used to pass information from one tentacle to the main process
        self.out_queue = multiprocessing.Queue()

        #List of current tentacles (will be populated in start)
        self.cur_tentacles = list()

        #Schedule checking every ten seconds out_queue to see if some tentacle has brought back stuff
        self.num_cur_downloads = 0

    def _start_sched_out_queue(self):
        #Start periodic check only if it is not already started
        if self.num_cur_downloads == 0:
            logging.debug('Start scheduled check of self.out_queue every 5 seconds')
            self.schedule('check_out_queue', 5, self._task_check_out_queue, repeat=True)

    def _stop_sched_out_queue(self):
        logging.debug("Stopping scheduled check of self.out_queue")
        self.scheduler.remove('check_out_queue')

    def _task_check_out_queue(self):
        if self.num_cur_downloads > 0:
            try:
                done_task = self.out_queue.get(block = False)
                who, message = done_task
            except multiprocessing.queues.Empty:
                pass #The queue is empty, no actions
            else:
                self.num_cur_downloads -= 1
                self.send_message(who, message)
        if self.num_cur_downloads == 0:
            self._stop_sched_out_queue()

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        self.get_roster()

        #for each worker create an in_queue used to send download tasks to that
        #specific worker (or pool of)
        for x in tentacles.ALL:
            logging.info('Preparing %s' % x.WClassName)
            q = multiprocessing.Queue()
            worker = getattr(x, x.WClassName)
            t = worker(q, self.out_queue, self.config)
            t.start()
            self.cur_tentacles.append((t, q))

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """

        jid_full = msg['from']
        jid_bare = msg['from'].bare

        #check only on bare username
        if not jid_bare in self.config.allowed_users:
            return

        if msg['type'] in ('chat', 'normal'):
            #Strip whitespace, split on space and keep only the first portion
            message = msg['body'].strip().split(" ")[0]

            thing = Thing(message)
            #Check which worker can handle the link, the first that can wins
            #and the loop stops
            tentacle_found = False
            for t, q in self.cur_tentacles:
                if t.supports(thing):
                    logging.debug("%s supports %s" % (t.__class__, thing.url.href()))
                    self._start_sched_out_queue()
                    msg.reply(random.choice(CONFIRM)).send()
                    q.put((jid_full, thing))
                    self.num_cur_downloads += 1
                    tentacle_found = True
                    break

            if not tentacle_found:
                logging.debug("No valid tentacles found for processing %s" % message)
                msg.reply(random.choice(UNRECOGNIZED)).send()

                #dopo il break appare il seguente errore
                """Traceback (most recent call last):
                     File "/usr/lib/python2.7/multiprocessing/queues.py", line 266, in _feed
                       send(obj)
                   TypeError: expected string or Unicode object, NoneType found
                   """

                #vedi qui http://stackoverflow.com/questions/10607553/python-multiprocessing-queue-what-to-do-when-the-receiving-process-quits

    #THE following two methods are only kept for
    #reference purposes, on how to launch a subprocess if necessary

    def youtube_video_id(self, link):
        """Given the youtube video url returns the id or None if there is no match"""
        #http://stackoverflow.com/questions/2964678/jquery-youtube-url-validation-with-regex/10315969#10315969
        yrx = r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$"
        import re
        match = re.search(yrx, link)
        if match:
            yid = match.group(1)
        else:
            yid = None

        return yid

    def youtube_dl_subprocess(self, yid):
        """Given a youtube video id it executes youtube-dl to download it"""
        yurl = "http://www.youtube.com/watch?v=%s" % yid
        import subprocess
        #output = subprocess.Popen(['youtube-dl', yurl], shell=True, stdout=subprocess.PIPE).stdout.read()
        output = subprocess.Popen("youtube-dl %s" % yurl,
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)  #.stdout.read()
        #stuff = output.stdout.read()
        #print 'Have %d bytes in output' % len(stuff)
        #print stuff

if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    logging.getLogger().setLevel(level=logging.DEBUG)

    #opts.loglevel = logging.DEBUG
    #logging.basicConfig(level=opts.loglevel,
    #                    format='%(levelname)-8s %(message)s')

    import tconfig

    try:
        config = tconfig.TConfig()
    except tconfig.ConfigurationException, e:
        logging.error(e)
        sys.exit(2)

    # Setup the TentacleBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = TentacleBot(config)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199') # XMPP Ping

    # If you are working with an OpenFire server, you may need
    # to adjust the SSL version used:
    # xmpp.ssl_version = ssl.PROTOCOL_SSLv3

    # If you want to verify the SSL certificates offered by a server:
    # xmpp.ca_certs = "path/to/ca/cert"

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")