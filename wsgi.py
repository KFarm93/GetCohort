#!/usr/bin/python
import sys
import logging
import os
logging.basicConfig(stream=sys.stderr)
path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, path)

# server = server.py
# if the name of my file is phonebook.py then the following code would apply:
# from phonebook import app as application
from server import app as application
