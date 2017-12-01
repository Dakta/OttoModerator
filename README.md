# OttoModerator

A moderation bot for Reddit, based on AutoModerator.

In AutoModerator, configuration comprises a collection of Rules. Each Rule is itself a mixed collection of Match Conditions and response Actions. The match conditions specify criteria for selecting posts and comments, which are then responded to by the actions. For example:

    ---
    # these are the conditions: 
    title (contains): ["Some", "shitpost", "phrases"]
    kind: 'post' # redundant, but whatever
    reports: 2 # at least two reports
    # these are the responses:
    action: remove
    comment: 'No shitposts'
    ---

Besides convention, there is no clear distinction between the matching conditions and the responses. There's also no way to take the same set of responses to a variety of conditions except by copy-paste duplication of the responses section. These rules are highly constrained, as they must select the `thing` (the Reddit codebase calls posts, comments, and all other data points a `thing`) itself that you want to act on.

Some kinds of contextual information can be selected by using ["sub-groups"](https://www.reddit.com/wiki/automoderator/full-documentation#wiki_sub-groups), an ungainly solution which is still highly limited. For example, you can check some things about the user account associated with the matched `thing`, as well as checking some things about the parent submission of matched comment items. See the example at the link, it's just atrocious:

    ---
    # this example sets sumbmission flair if a known/approved user calls it a repost
    type: comment
    body: "repost"
    is_top_level: true
    author:
        # this is a matching condition
        flair_css_class: "trusted"
    parent_submission:
        # but this is a reaction
        set_flair: "Possible Repost"s
    ---

I wanted a better way: to cleanly and clearly separate the matching conditions from the responses, to be able to group multiple sets of different matching criteria and have the same response, and to be able to target arbitrary contextual information for matching and response. For example, we can set different report thresholds for comments and posts:

    ---
    criteria:
        - type: post
          reports: 5
        - type: comment
          reports: 2
    actions:
        action: remove
    ---

Or we should be able to remove both comments and submissions based on reply by trusted user, locking and sticky-ing the comment if it's a submission:

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
            lock: true
            reply (sticky): "This {{parent.type}} has been removed: {{match-1}}"
    ---

This should give a flavor for the eventual capabilities of this bot, and its clear advantages over AutoModerator. Note that the examples are probably not yet functional.

# Requirements

Python: 3.6.3
Others: see requirements.txt

Top level dependencies are recorded in `requirements.txt`. An exact list of
operational state dependencies is recorded in `requirements.deploy.txt`. The
former is used during development to maintain the actual dependencies of the
project. The latter is used for deployment to ensure exact version
compatibility. [Based on Kenneth Jones'
workflow](https://www.kennethreitz.org/essays/a-better-pip-workflow).

During initial project setup, use `pip install -r
requirements.depoly.txt` to ensure compatibility with known functional
versions.

During development, keep dependencies up to date:

1. Add or update entries in `requirements.txt`

2. Get the latest versions: `pip install -U -r requirements.txt`

3. Record the last working state: `pip freeze > requirements.deploy.txt`

# Status

**Warning:** this project is nowhere near fully functional and should not under any circumstances be used in production.