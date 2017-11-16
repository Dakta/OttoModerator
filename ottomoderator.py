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

# bot configuration parsing
import yaml

# for debugging
import pprint


# global reddit session
r = None




class Criteria:
    """A set of conditions for matching Actions against reddit content"""
    
    def __init__(self, values):
        pass

    def matches(self, item):
        for condition in self.conditions:
            if not condition.matches(item):
                return False

        return True


class Action:
    """A sequence of steps to perform on and in response to reddit content"""
    pass

class Rule:
    """A collection of conditions and response actions triggered on matching content"""

    def __init__(self, values):
        # TODO lowercase keys

        self.yaml = yaml.dump(values)

        # Handle single/multiple criteria
        self.criteria = []
        if isinstance(values["criteria"], list):
            for criteria in values["criteria"]:
                self.criteria.append(new Criteria(criteria))
        elif isinstance(values["criteria"], dict):
            self.criteria.append(new Criteria(values["criteria"]))

        # same for actions
        self.actions = []
        if isinstance(values["actions"], list):
            for action in values["actions"]:
                self.actions.append(new Action(action))
        elif isinstance(values["actions"], dict):
            self.actions.append(new Action(values["actions"]))
        # TODO consolidate the above two blocks, cleverly


    def matches(self, item):
        # for reference later?
        self.matches = []

        for criteria in self.criteria:
            if criteria.matches(item):
                self.matches.append(criteria.name)

        if len(self.matches) > 0:
            return True

    def _perform_actions_on(self, item):
        for action in self.actions:
            actions.perform_on(item)

    def process(self, item):
        if self.matches(item):
            self._perform_actions_on(item)



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

def update_rules_for_sr(rule_dict, subreddit): # , queues):
    rule_dict[subreddit.name] = {}
    rules = [Rule(d)
                for d in yaml.safe_load_all(subreddit.conditions_yaml)
                if isinstance(d, dict)]
    # for queue in queues:
    #     cond_dict[subreddit.name][queue] = filter_conditions(conditions, queue)


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

    """
    global r

    for message in r.inbox.unread(limit=None):
        # pprint.pprint(repr(message))
        # pprint.pprint(vars(message))

        if isinstance(message, praw.models.Message) and message.new:
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
            # break
        except Exception as e:
            logger.error('ERROR: {0}'.format(e))
            logger.debug(traceback.format_exc())
        else:
            sr_dict = get_moderated_subreddits()

            # load conditions from wiki
            rule_dict = load_all_rules(sr_dict)

            break

    while True:
        # main execution loop
        try:
            # First, process command messages
            for message in unread_messages():
                try:
                    command = message.body.strip().lower()
                    if command == 'register':
                        # try to accept mod invite
                        sr_name = clean_sr_name(message.subject).lower()
                        subreddit = r.subreddit(sr_name)

                        try:
                            subreddit.mod.accept_invite()
                        except:
                            message.reply("You must invite me to moderate /r/{} first."
                                          .format(sr_name))
                        else:
                            # get sub from db:
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
                                # now that it definitely exists: set enabled (flush old rules?)
                                db_subreddit.enabled = True
                                session.commit()
                            message.reply("I have joined /r/{}".format(db_subreddit.name))
                    elif command in ['update', 'status', 'enable', 'disable', 'leave']:
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
                                # TODO reload mod subs
                            elif command == 'disable':
                                db_subreddit.enabled = False
                                # TODO reload mod subs
                            elif command == 'leave':
                                # leave moderator of subreddit
                                if db_subreddit.enabled:
                                    message.reply("Please disable me on this subreddit first.")
                                else:
                                    # TODO not implemented yet
                                    # TODO reload mod subs
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

