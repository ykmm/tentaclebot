Tentaclebot
===========

#### This is pre-ante-un-alpha software, for the love of your family and pets, be careful! ####

A multipurpose jabber bot tasked to grab stuff in the internets and download them locally. Because offline is better!

At the moment it supports downloading all the videos that are supported by youtube-dl and answering in the most servile and submissive way.

Installation
------------

* required python modules: python-yaml, python-sleekxmpp, python-pycurl
* required application: youtube-dl (install last version with pip install)

Edit the contents of the file tconfig.yaml and set username, password, and allowed users.
You can also create a file named tconfig-local.yaml (local development configuration file) that will override tconfig.yaml.