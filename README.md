Tentaclebot
===========

#### This is very alpha software, for the love of your family and pets, be careful! ####

A multipurpose jabber bot tasked to grab stuff in the internets and download them locally. Because offline is better!

Features
--------

* Downloads everything and stores it using the mimetype rules from the configuration file
* Custom support for video streaming sites (all the websites supported by youtube-dl)
* Answers in the most servile and submissive way
* Supports distinct conversations with only allowed_users

Installation
------------

* required python modules: python-yaml, python-sleekxmpp, python-pycurl, python-magic
* required application: youtube-dl (install last version with pip install)

Edit the contents of the file tconfig.yaml and set username, password, and allowed users.
You can also create a file named tconfig-local.yaml (local development configuration file) that will override tconfig.yaml.