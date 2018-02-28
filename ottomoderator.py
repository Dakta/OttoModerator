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

# Rules functionality
from rules import *

# API wrapper
import praw, prawcore

# bot configuration parsing
import yaml

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

    # TODO: this is redundant now
    if message.author not in subreddit.moderator():
        message.reply('Error: You do not moderate /r/{0}'.format(subreddit.display_name))
        return

    # TODO: validate wiki permissions?

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

def update_rules_for_sr(rule_dict, subreddit): # , queues):
    rule_dict[subreddit.name] = {}

    logger.debug("Yaml loading rules for /r/{}".format(subreddit.name))
    for d in yaml.safe_load_all(subreddit.conditions_yaml):
        pprint.pprint(d)
    # pprint.pprint(yaml.safe_load_all(subreddit.conditions_yaml))

    rules = [Rule(d)
                for d in yaml.safe_load_all(subreddit.conditions_yaml)
                if isinstance(d, dict)]

    # for queue in queues:
    #     cond_dict[subreddit.name][queue] = filter_conditions(conditions, queue)

    rule_dict[subreddit.name] = rules


def load_all_rules(sr_dict): # , queues):
    rule_dict = {}
    for sr in sr_dict.values():
        update_rules_for_sr(rule_dict, sr) # , queues)

    return rule_dict


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

    Also, checking if an inbox item is a PM requires weeding out SubredditMessage types,
    which are also (logically, but annoyingly), Message types.

    """
    global r

    for message in r.inbox.unread(limit=None):
        # pprint.pprint(repr(message))
        # pprint.pprint(isinstance(message, praw.models.Message))
        # pprint.pprint(vars(message))

        # annoyingly, we have to check whether something is a Message and *not* a SubredditMessage
        if (isinstance(message, praw.models.Message) and
            not isinstance(message, praw.models.SubredditMessage) and
            message.new):
            # ugh
            yield message

def get_moderated_subreddits():
    # get enabled subreddits
    subreddits = (session.query(Subreddit)
                  .filter(Subreddit.enabled == True)
                  .all())

    # we gotta refresh the list of modded subs
    logger.info('Getting list of moderated subreddits')
    modded_subs = [sr.display_name.lower() for sr in r.user.moderator_subreddits(limit=None)]

    # get rid of any subreddits the bot doesn't moderate
    # TODO: disable the ones we don't mod? Send an error message to modmail?
    sr_dict = {sr.name.lower(): sr
               for sr in subreddits
               if sr.name.lower() in modded_subs}

    return sr_dict



def build_multireddit_groups(subreddits):
    """Splits a subreddit list into groups if necessary (due to url length)."""
    multireddits = []
    current_multi = []
    current_len = 0
    for sub in subreddits:
        if current_len > 3300:
            multireddits.append(current_multi)
            current_multi = []
            current_len = 0
        current_multi.append(sub)
        current_len += len(sub) + 1
    multireddits.append(current_multi)

    return multireddits


def main():
    global r

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
            # break
        except Exception as e:
            logger.error('ERROR: {0}'.format(e))
            logger.debug(traceback.format_exc())
        else:
            sr_dict = get_moderated_subreddits()

            # load conditions from wiki
            rule_dict = load_all_rules(sr_dict)

            pprint.pprint(rule_dict)

            break

    while True:
        # main execution loop

        sleep_after = True
        reload_mod_subs = False

        try:
            # First, process command messages
            for message in unread_messages():
                try:
                    command = message.body.strip().lower()
                    sr_name = clean_sr_name(message.subject).lower()
                    subreddit = r.subreddit(sr_name)
                    # TODO: validate user is moderator
                    if message.author not in subreddit.moderator():
                        message.reply('Error: You do not moderate /r/{0}'.format(subreddit.display_name))
                        continue
                    # OK, validated
                    if command == 'register':
                        # do we know this sub?
                        if sr_name in sr_dict.keys():
                            message.reply("I already moderate /r/{}.\n\n".format(sr_name))
                            continue

                        # otherwise... try to accept mod invite
                        try:
                            subreddit.mod.accept_invite()
                        except:
                            # should be APIException(error_type='NO_INVITE_FOUND')
                            message.reply("You must invite me to moderate /r/{} first."
                                          .format(sr_name))
                            raise
                        else:
                            # get sub from db if previously registered:
                            db_subreddit = None
                            try:
                                db_subreddit = (session.query(Subreddit)
                                               .filter(Subreddit.name == sr_name)
                                               .one())
                            except NoResultFound:
                                # add to DB
                                db_subreddit = Subreddit()
                                db_subreddit.name = subreddit.display_name.lower()
                                db_subreddit.last_submission = datetime.utcnow() - timedelta(days=1)
                                db_subreddit.last_spam = datetime.utcnow() - timedelta(days=1)
                                db_subreddit.last_comment = datetime.utcnow() - timedelta(days=1)
                                db_subreddit.conditions_yaml = ''
                                session.add(db_subreddit)
                            finally:
                                # now that it definitely exists: set enabled
                                # (should we clear old rules from the db?)
                                db_subreddit.enabled = True
                                session.commit()
                            message.reply("I have joined /r/{}".format(db_subreddit.name))
                    elif command in ['update', 'status', 'enable', 'disable', 'leave']:
                        # these require the same database query
                        db_subreddit = None
                        try:
                            db_subreddit = (session.query(Subreddit)
                                           .filter(Subreddit.name == sr_name)
                                           .one())
                        except NoResultFound:
                            message.reply("Subreddit /r/{} is not registered with me."
                                          .format(sr_name))
                        else:
                            # only proceed if we get a database hit.
                            if command == 'update':
                                # refresh configuration for a subreddit
                                # todo: cache duplicate requests from multiple mods
                                reload_mod_subs = True
                                update_from_wiki(db_subreddit, message)
                            elif command == 'status':
                                pass
                            elif command == 'enable':
                                db_subreddit.enabled = True
                                reload_mod_subs = True
                            elif command == 'disable':
                                db_subreddit.enabled = False
                                reload_mod_subs = True
                            elif command == 'leave':
                                # leave moderator of subreddit
                                if db_subreddit.enabled:
                                    message.reply("Please disable me on this subreddit first.")
                                else:
                                    # TODO not implemented yet
                                    reload_mod_subs = True
                                    raise NotImplementedError
                            # the following commands should respond with the enabled status
                            if command in ['status', 'enable', 'disable']:
                                message.reply("Subreddit /r/{} is currently {}abled."
                                              .format(db_subreddit.name,
                                                      'en' if db_subreddit.enabled else 'dis'))
                        finally:
                            session.commit()
                    elif command == 'help':
                        # should this just provide a link, or real command explanations?
                        raise NotImplementedError
                    else:
                        # invalid command
                        message.reply("Invalid command.")
                except NotImplementedError:
                    message.reply("Error: that feature is not yet implemented.")
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error('ERROR: {0}'.format(e))
                    logger.debug(traceback.format_exc())
                    message.reply("# ERROR:\n\n{}".format(indent_lines(str(e))))
                finally:
                    message.mark_read()

            # changed mod subs
            if reload_mod_subs:
                sr_dict = get_moderated_subreddits()
                rule_dict = load_all_rules(sr_dict)

            # Then process queues: submission, comment, spam, report, comment reply, username mention
            # TODO: queue for edited items...

            # Queue priority, in increasing specificity:
            # - reports: multi/about/reports?only=(links|comments)
            #   - comment
            #   - submission
            #   - any
            # - spam: multi/about/spam?only=(links|comments)
            #   - comment
            #   - submission
            #   - any
            # - edited: multi/about/edited?only=(links|comments)
            #   - comment
            #   - submission
            #   - any
            # - reply: inbox
            # - mention: inbox
            # - submission: multi/new
            # - comment: multi/comments

            multi_mod_queues = ['reports', 'spam', 'edited'] # r.subreddit().mod.<q>
            multi_queues = ['new', 'comments'] # r.subreddit().<q>
            user_queues = ['comment_replies', 'submission_replies', 'mentions'] # r.user.inbox.<q>

            # proof of concept
            for sr_name, subreddit in sr_dict.items():
                logger.debug("Checking items in /r/{}".format(sr_name))

                sr = r.subreddit(sr_name)

                # mod-only level queues
                for item in sr.mod.spam():
                    for rule in rule_dict[sr_name]:
                        rule.process(item)
                for item in sr.mod.reports():
                    for rule in rule_dict[sr_name]:
                        rule.process(item)
                for item in sr.mod.edited():
                    for rule in rule_dict[sr_name]:
                        rule.process(item)

                # sub-level queues
                for item in sr.mod.new():
                    for rule in rule_dict[sr_name]:
                        rule.process(item)
                for item in sr.mod.comments():
                    for rule in rule_dict[sr_name]:
                        rule.process(item)

                # user queues - not implemented


            # for queue in queue_funcs:
            #     subreddits = [s for s in sr_dict
            #                   if s in cond_dict and len(cond_dict[s][queue]) > 0]
            #     if len(subreddits) == 0:
            #         continue

            #     multireddits = build_multireddit_groups(subreddits)

            #     # fetch and process the items for each multireddit
            #     for multi in multireddits:
            #         if queue == 'report':
            #             limit = cfg_file.get('reddit', 'report_backlog_limit_hours')
            #             stop_time = datetime.utcnow() - timedelta(hours=int(limit))
            #         else:
            #             stop_time = max(getattr(sr, 'last_'+queue)
            #                              for sr in sr_dict.values()
            #                              if sr.name in multi)

            #         queue_subreddit = r.get_subreddit('+'.join(multi))
            #         if queue_subreddit:
            #             queue_func = getattr(queue_subreddit, queue_funcs[queue])
            #             items = queue_func(limit=None)
            #             check_items(queue, items, stop_time, sr_dict, cond_dict)



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

