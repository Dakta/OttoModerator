# OttoModerator
A moderation bot for Reddit, based on AutoModerator.


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

