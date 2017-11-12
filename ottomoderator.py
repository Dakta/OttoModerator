#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from time import sleep
from sqlalchemy.orm.exc import NoResultFound
import sys, traceback

# set up logging
from config import logging
logger = logging.getLogger(__name__)
# pull config file
from config import cfg_file

# get database connection
from models import session
from models import Subreddit

# API wrapper
import praw, prawcore

# for debugging
import pprint


# global reddit session
r = None


def update_from_wiki(db_subreddit, message):
    """Updates conditions from the subreddit's wiki."""

    global r
    username = cfg_file.get('reddit', 'username')
    wiki_page_name = cfg_file.get('bot', 'wiki_page_name')

    subreddit = r.subreddit(db_subreddit.name)

    if requester not in subreddit.moderator():
        message.reply('Error: You do not moderate /r/{0}'.format(subreddit.display_name))
        return

    # TODO: validate wiki permissions

    try:
        page_content = subreddit.wiki[wiki_page_name].content_md
    except Exception:
        message.reply('The wiki page could not be accessed. Please ensure the page '
                      'http://www.reddit.com/r/{0}/wiki/{1} exists and that {2} '
                      'has the "wiki" mod permission to be able to access it.'
                      .format(subreddit.display_name,
                              wiki_page_name,
                              username))
        # raise
        return False

    # TODO: validate and parse rules? Maybe do that somewhere else.

    db_subreddit.conditions_yaml = page_content
    session.commit()

    message.reply("{0}'s conditions were successfully updated for /r/{1}"
                  .format(username, subreddit.display_name))
    return True

def indent_lines(lines):
    """Formatter for Markdown messages to generate code block from `lines`"""
    indented = ''
    for line in lines.split('\n'):
        indented += '    {0}\n'.format(line)
    return indented


def clean_sr_name(text):
    # trim reply notice
    # might belong elsewhere, but here is quite robust
    if text.startswith('re: '):
        text = text[4:]

    # handle if they put in something like '/r/' in the subject
    if '/' in text:
        cleaned = text[text.rindex('/')+1:]
    else:
        cleaned = text
    # We could single-line this...
    return cleaned.strip()


def error_message(sr_name, error):
    """Formats an error message for return to user if a wiki update failed."""

    return ('### Error updating from [wiki configuration in /r/{0}]'
            '(/r/{0}/wiki/{1}):\n\n---\n\n{2}\n\n---\n\n'
            '[View configuration documentation](https://'
            'github.com/Dakta/OttoModerator/wiki/Wiki-Configuration)'
            .format(sr_name,
                    cfg_file.get('bot', 'wiki_page_name'),
                    error))


def unread_messages():
    """Wraps r.inbox.unread() and returns only the unread,
    non-SubredditMessage ones.

    Why? Because /message/messages has been broken (only returns top level message of
    conversation threads), and /message/messages/unread no longer works:
    https://www.reddit.com/r/changelog/comments/6sfacz/-/dlcfjib/

    """
    global r

    for message in r.inbox.unread(limit=None):
        # pprint.pprint(repr(message))
        # pprint.pprint(vars(message))

        if isinstance(message, praw.models.Message) and message.new:
            yield message


def main():
    global r
    sleep_after = True

    prawlogger = logging.getLogger('prawcore')
    prawlogger.setLevel(logging.WARN)

    while True:
        # Login retry loop
        try:
            logger.info('Logging in as {0}'
                        .format(cfg_file.get('reddit', 'username')))
            r = praw.Reddit(client_id     = cfg_file.get('reddit', 'client_id'),
                            client_secret = cfg_file.get('reddit', 'client_secret'),
                            user_agent    = cfg_file.get('reddit', 'user_agent'),
                            username      = cfg_file.get('reddit', 'username'),
                            password      = cfg_file.get('reddit', 'password'))
            break
        except Exception as e:
            logger.error('ERROR: {0}'.format(e))
            logger.debug(traceback.format_exc())

    while True:
        # main execution loop
        try:
            # First, process command messages
            for message in unread_messages():
                try:
                    command = message.body.strip().lower()
                    if command in ['update', 'status', 'enable', 'disable', 'leave']:
                        # these require a database query
                        sr_name = clean_sr_name(message.subject).lower()
                        db_subreddit = None
                        try:
                            db_subreddit = (session.query(Subreddit)
                                           .filter(Subreddit.name == sr_name)
                                           .one())
                        except NoResultFound:
                            message.reply("Subreddit /r/{} is not registered with /u/{}."
                                          .format(sr_name, cfg_file.get('reddit', 'username')))
                        else:
                            # only proceed if we get a database hit.
                            if command == 'update':
                                # refresh configuration for a subreddit
                                # todo: cache duplicate requests from multiple mods
                                update_from_wiki(sr_name, message.author)
                            elif command == 'status':
                                pass
                            elif command == 'enable':
                                db_subreddit.enabled = True
                            elif command == 'disable':
                                db_subreddit.enabled = False
                            elif command == 'leave':
                                # leave moderator of subreddit
                                if db_subreddit.enabled:
                                    message.reply("Please disable me on this subreddit first.")
                                else:
                                    # TODO not implemented yet
                                    raise NotImplementedError

                            # the following commands should respond with the enabled status
                            if command in ['status', 'enable', 'disable']:
                                message.reply("Subreddit /r/{} is currently {}abled."
                                              .format(db_subreddit.name,
                                                      'en' if db_subreddit.enabled else 'dis'))
                        finally:
                            # session commit?
                            pass

                    elif command == 'register':
                        # not sure whether what the prodecure for this one should be yet...
                        message.reply("# Error\n\nNot implemented.")
                    else:
                        # invalid command
                        message.reply("Invalid command.")
                except NotImplementedError:
                    message.reply("Error: that feature is not yet implemented.")
                except Exception as e:
                    logger.error('ERROR: {0}'.format(e))
                    logger.debug(traceback.format_exc())
                    message.reply("# ERROR:\n\n{}".format(indent_lines(str(e))))
                finally:
                    message.mark_read()


            # Then process queues: submission, comment, spam, report, comment reply, username mention


        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error('ERROR: {0}'.format(e))
            logger.debug(traceback.format_exc())
            session.rollback()
        finally:
            if sleep_after:
                logger.info('Sleeping for 10 seconds')
                sleep(10)
                logger.info('Sleep ended, resuming')

        logging.info("Looping")


if __name__ == '__main__':
    main()

