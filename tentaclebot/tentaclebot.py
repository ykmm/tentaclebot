#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    TentacleBOT: The Offlineator!
"""

import sys
import logging
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

class TentacleBot(sleekxmpp.ClientXMPP):
    """
    A simple SleekXMPP bot that will echo messages it
    receives, along with a short thank you message.
    """

    def __init__(self, jid, password, allowed_users):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

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
        self.allowed_users = allowed_users

        #IN and OUT queues used to pass information to the single tentacles
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()

        #Create a pool of workers
        cur_tentacles = [tentacles.youtubedl.Worker(self.in_queue, self.out_queue)]
        for w in cur_tentacles:
            w.start()

        #Schedule checking every ten seconds out_queue to see if some tentacle has brought back stuff
        self.schedule('check_out_queue', 10, self._task_check_out_queue, repeat=True)
        self.scheduler.remove
        self.num_cur_downloads = 0

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

        if not msg['from'].bare in self.allowed_users:
            return

        who = msg['from'].bare
        if msg['type'] in ('chat', 'normal'):
            #Strip whitespace, split on space and keep only the first portion
            body = msg['body'].strip()
            body = body.split(" ")[0]
            #prepend it with a 'http://' if it is missing
            if not (body.startswith('http://') or body.startswith('https://')):
                body = 'http://'+body

            #Check which worker can handle the link

            #If it is a video url, pass it directly to youtube-dl
            if tentacles.youtubedl.supported(body):
                msg.reply(random.choice(CONFIRM)).send()
                self.in_queue.put((who, body))
                self.num_cur_downloads += 1
            #otherwise, dereference the url and have it analyzed and processed by the relative worker
            else:
                from docextractor.docextractor import DocExtractor, pycurl
                DE = DocExtractor()
                try:
                    http_code, http_data = DE.get_url(body)
                except pycurl.error:
                    msg.reply(random.choice(UNRECOGNIZED)).send()
                else:
                    print http_code, http_data
                msg.reply(random.choice(UNRECOGNIZED)).send()

            #THIS commented code, and the following two methods are only kept for
            #reference purposes, on how to launch a subprocess if necessary

            #yid = self.youtube_video_id(body)
            #if yid is not None:
            #
            #    self.youtube_dl_subprocess(yid)
            #else:
            #
            #    #msg.reply("Thanks for sending\n%(body)s" % msg).send()

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
    opts.loglevel = logging.DEBUG
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    try:
        f = open('tconfig.yaml')
    except IOError:
        main_conf = False
    else:
        main_conf = True
        conf_data = yaml.safe_load(f)
        f.close()
        opts.jid = conf_data['username']
        opts.password = conf_data['password']

    try:
        f = open('tconfig-local.yaml')
    except IOError:
        local_conf = False
    else:
        local_conf = True
        conf_data = yaml.safe_load(f)
        f.close()
        opts.jid = conf_data['username']
        opts.password = conf_data['password']

    if not main_conf and not local_conf:
        if opts.jid is None:
            opts.jid = raw_input("Username: ")
        if opts.password is None:
            opts.password = getpass.getpass("Password: ")


    # Setup the TentacleBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = TentacleBot(opts.jid, opts.password, conf_data['allowed_users'])
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