# SALT Storage Service

A service for storing proposal content for the Southern African Large Telescope (SALT).

## Prerequisites

Python 3.8 must be installed for running the service.

## Environment variables

The following environment variables need to be defined, preferably in the `.env` file.

Variable name | Description | Example
--- | --- | ---
CONVERT_COMMAND | Comma d for converting images | /usr/bin/convert
DATABASE_URL | DSN for the database. | mysql://username:password@my.database.server:3306/my_database
EPHEMERIS_URL | URL for requesting asteroid ephemerides | http://pysalt.salt.ac.za/finder_chart/ephemerides.cgi
FINDER_CHART_TOOL | Command for generating finer charts | saltfc
MAPPING_TOOL_API_KEY | API key for using the mapping tool | ABcd1234 
PIPT_DIR | Directory used for storing PIPT related files | /home/user/.PIPT
SALT_API_PUBLIC_KEY_FILE | File where the public key of the SALT API server is stored | /server/salt_api_server_key.pub
SENTRY_DSN | DSN for recording exceptions with Sentry | http://xyz123@sentry.io/1234567
WEB_MANAGER_DIR | Directory in which Web Manager content is stored | /home/user/wm
WEB_MANAGER_URL | URL of the Web Manager | https://www.salt.ac.za/wm


## Running the server for development

Make sure that [poetry](https://python-poetry.org) is installed on your machine and run the following command.

```shell script
poetry install
```

You can then launch the server as follows.

```shell script
poetry run uvicorn storage.app:app --reload
```

The `--reload` flag is optional; it ensures that the server is restarted when files change.

