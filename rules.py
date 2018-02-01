# # set up logging
# from config import logging
# logger = logging.getLogger(__name__)


# import re


class Criterion:
    """A set of conditions for matching Actions against PRAW objects"""

    def __init__(self, values):
        # convert the dict to attributes
        self.conditions = values
        self.modifiers = dict()

        # re-duplicate concatenated targets
        # parse out modifiers
        target_syntax = re.compile(r'^(?P<targets>[a-z0-9\_\+]+)(?P<modifiers>\([a-z0-9\_,]*\))?$')
        for k, v in self.conditions.items():
            parts = target_syntax.match(k)
            # now split the targets and modifiers
            # targets = []
            # modifiers = []
            # for target in targets:
            #     self.conditions[target] = v
            #     self.modifiers[target] = modifiers

    def matches(self, item):
        logger.debug("Checking item {}".format(item))
        # Conditions are in self.__dict__
        for condition, value in self.conditions.items():
            logger.debug("- Checking `{}` for `{}`".format(condition, value))



            # uhhhh... this is kinda scary
            if not getattr(item, condition, None) == value:
                return False

        # for condition in self.conditions:
        #     if not condition.matches(item):
        #         return False

        return True


class Action:
    """A sequence of steps to perform on and in response to reddit content"""

    def __init__(self, values):
        self.actions = values

    def perform_on(self, item):
        for action, argument in self.actions.items():
            method = getattr(item, action, getattr(item.mod, action, None))
            if method:
                method(argument)
            else:
                raise AttributeError("No such method {} on {}".format(method, item))

class Rule:
    """A collection of conditions and response actions triggered on matching content"""

    def __init__(self, values):
        # TODO lowercase keys
        logger.debug("Creating new rule...")

        self.yaml = yaml.dump(values)

        # Handle single/multiple criteria
        self.criteria = []
        if isinstance(values["criteria"], list):
            for criterion in values["criteria"]:
                self.criteria.append(Criterion(criterion))
        elif isinstance(values["criteria"], dict):
            self.criteria.append(Criterion(values["criteria"]))

        # same for actions
        self.actions = []
        if isinstance(values["actions"], list):
            for action in values["actions"]:
                self.actions.append(Action(action))
        elif isinstance(values["actions"], dict):
            self.actions.append(Action(values["actions"]))
        # TODO consolidate the above two blocks, cleverly

        pprint.pprint(vars(self))
        for c in self.criteria:
            pprint.pprint(vars(c))
        for a in self.actions:
            pprint.pprint(vars(a))


    def matches(self, item):
        # for reference later?
        self.matched = []

        for criterion in self.criteria:
            if criterion.matches(item):
                self.matched.append(criterion)

        if len(self.matched) > 0:
            return True

    def _perform_actions_on(self, item):
        for action in self.actions:
            action.perform_on(item)

    def process(self, item):
        if self.matches(item):
            logger.debug("Matched {}".format(item))
            self._perform_actions_on(item)

