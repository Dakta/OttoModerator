#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from sqlalchemy.orm.exc import NoResultFound


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

# get database connection
from models import session
from models import Subreddit

# populate our moderated subreddits
for sr in reddit.user.moderator_subreddits():
    try:
        db_subreddit = (session.query(Subreddit)
                       .filter(Subreddit.name == sr.display_name.lower())
                       .one())
    except NoResultFound:
        logger.info("Adding subreddit /r/{} to database".format(sr.display_name))
        db_subreddit = Subreddit()
        db_subreddit.name = sr.display_name.lower()
        db_subreddit.last_submission = datetime.utcnow() - timedelta(days=1)
        db_subreddit.last_spam = datetime.utcnow() - timedelta(days=1)
        db_subreddit.last_comment = datetime.utcnow() - timedelta(days=1)
        session.add(db_subreddit)

session.commit()

