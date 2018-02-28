# Configuration

This document provides a guide for end users of the OttoModerator service (presumably /u/OttoModBot), please see `README.md` for standalone installation information.

## Setup/Getting Started

Before you can use OttoModerator you must invite it to moderate your subreddit. The classic caveats of AutoModerator apply: for full functionality, the bot needs full permissions.

1. Invite /u/OttoModBot to moderate your subreddit: `reddit.com/r/YOUR_SUB/about/moderators`
2. Tell /u/OttoModBot to accept the invite: `reddit.com/message/compose?to=OttoModBot&subject=YOUR_SUB&message=register`
3. Create the configuration wiki page: `reddit.com/r/YOUR_SUB/wiki/create/ottomoderator`. Add this header as a reminder:
        ###### If you edit this page, you must [click this link, then click "send"](http://www.reddit.com/message/compose/?to=OttoModBot&subject=YOUR_SUB&message=update) to have AutoModerator re-load the rules from here
4. (Recommended) Lock down the wiki page: select "only mods may edit and view" on `reddit.com/r/YOUR_SUB/wiki/settings/ottomoderator`. If you have a public wiki, this is *strongly* recommended. However, it is not enforced, which means you can easily shoot yourself in the foot by allowing any user to edit your wiki page. Since wiki updates must be manually triggered by a subreddit's moderators (see next step), it shouldn't present a security risk, but this is *not* recommended.

## Monitoring/Controlling

OttoModerator is managed by simple commands over Reddit PM:

Subject: YOUR_SUB
Message: command

For a listing of currently supported commands, use `help`: `reddit.com/message/compose?to=OttoModBot&subject=YOUR_SUB&message=help`

## Rules: An Overview

The basic configuration principles for OttoModerator are heavily inspired by AutoModerator. The principal difference is that matching conditions are separated from response actions, as such:

    ---
    criteria:
        type: ['post', 'comment', 'modmail', 'mention']
        title: 'foo regex' # dependent on 'post' or 'modmail', ignored otherwise
        body: 'bar regex' # all types
    actions:
        report: 'Reason text'
        action: spam, ham, approve # Note: setting modlog action reasons are not supported by the API
    ---

The main reason for this is to support arbitrary combinations of criteria and actions, so you can have multiple possible complex conditions trigger the same response:

    ---
    criteria:
        # list of multiple criteria
        - type: ['post', 'comment', 'modmail', 'mention']
          body: 'whatever'
        - type: ['post']
          reports: 3
        # ...

Another benefit is the ability to select arbitrary targets to respond to, so you're no longer limited to matching the exact `thing` you want your rule to act on:

    ---
    criteria:
        type: ['post', 'comment', 'modmail', 'mention']
        body: 'whatever'
    actions:
        # more complex
        parent:
            reply (distinguished): "Message text with {{substitutions}}"
    ---

A concrete example of this functionality is enabling trusted community members to trigger removal of posts:

    ---
    criteria:
        type: comment
        body (regex): "^\\!remove (.*)"
        is_reply: true
        author:
            contributor: true # let's make the approved submitters list useful
    actions:
        parent:
            action: remove
            lock: true # attempt to lock, if parent is a post
            reply (sticky): "This {{parent.type}} has been removed: {{match-1}}"
    ---

## Configuration Documentation

Currently supported: TODO

