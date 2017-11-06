from config import cfg_file


# Configure the database and access layer
from sqlalchemy import create_engine
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

if cfg_file.get('database', 'system').lower() == 'sqlite':
    engine = create_engine(
        cfg_file.get('database', 'system')+':///'+\
        cfg_file.get('database', 'database'))
else:
    engine = create_engine(
        cfg_file.get('database', 'system')+'://'+\
        cfg_file.get('database', 'username')+':'+\
        cfg_file.get('database', 'password')+'@'+\
        cfg_file.get('database', 'host')+'/'+\
        cfg_file.get('database', 'database'))



Base = declarative_base()
Session = sessionmaker(bind=engine, expire_on_commit=False)
session = Session()

# Initial setup:
# $ python
# >>> from models import *
# >>> Base.metadata.create_all(engine)

class Subreddit(Base):

    """Table containing the subreddits for the bot to monitor.

    name - The subreddit's name. "gaming", not "/r/gaming".
    enabled - Subreddit will not be checked if False
    conditions_yaml - YAML definition of the subreddit's conditions
    last_submission - The newest unfiltered submission the bot has seen
    last_comment - The newest comment the bot has seen
    last_spam - The newest filtered submission the bot has seen

    # unused; template for mirroring other subreddit configuration options
    exclude_banned_modqueue - Should mirror the same setting's value on the
        subreddit. Used to determine if it's necessary to check whether
        submitters in the modqueue are shadowbanned or not.
    """

    __tablename__ = 'subreddits'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)
    conditions_yaml = Column(Text)
    last_submission = Column(DateTime, nullable=False)
    last_comment = Column(DateTime, nullable=False)
    last_spam = Column(DateTime, nullable=False)
    # exclude_banned_modqueue = Column(Boolean, nullable=False, default=False)

