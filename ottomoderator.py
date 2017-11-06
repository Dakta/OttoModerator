#!/usr/bin/env python
# -*- coding: utf-8 -*-

# set up logging
from config import logging

logger = logging.getLogger(__name__)


# Log in to Reddit
import praw
from config import cfg_file

reddit = praw.Reddit(client_id     = cfg_file.get('reddit', 'client_id'),
                     client_secret = cfg_file.get('reddit', 'client_secret'),
                     user_agent    = cfg_file.get('reddit', 'user_agent'),
                     username      = cfg_file.get('reddit', 'username'),
                     password      = cfg_file.get('reddit', 'password'))

logger.info(reddit.read_only) # Should be False on successful login
logger.info(reddit.user.me())

