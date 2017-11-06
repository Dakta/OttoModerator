# Logging Samples

Sample configuration rules for BasicConfig logging. Kinda icky, should move to YAML instead.

## StdOut Only

    [loggers]
    keys = root

    [handlers]
    keys = roothand

    [formatters]
    keys = rootform

    [logger_root]
    level = INFO
    handlers = roothand

    [handler_roothand]
    class = StreamHandler
    formatter = rootform
    args = (sys.stdout,)

    [formatter_rootform]
    format = %(message)s

## StdOut and Named File

    [loggers]
    keys = root

    [handlers]
    keys = roothand,filehand

    [formatters]
    keys = rootform,fileform

    [logger_root]
    level = DEBUG
    handlers = roothand,filehand

    [handler_roothand]
    class = StreamHandler
    formatter = rootform
    args = (sys.stdout,)

    [handler_filehand]
    class = FileHandler
    level = DEBUG
    formatter = fileform
    args = ('automoderator.log', 'w')

    [formatter_rootform]
    format = %(message)s

    [formatter_fileform]
    format = %(asctime)s %(levelname)s %(message)s
