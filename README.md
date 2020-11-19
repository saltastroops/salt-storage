# SALT Storage Service

A service for storing proposal content for the Southern African Large Telescope (SALT).

## Prerequisites

Python 3.8 must be installed for running the service.

## Environment variables

The following environment variables need to be defined, preferably in the `.env` file.

Variable name | Description | Example
--- | --- | ---
DATABASE_URL | DSN for the database. | mysql://username:password@my.database.server:3306/my_database
SUBMIT_COMMAND | Command to execute for submitting the content (see below). | submit FILE
SUBMIT_DIRECTORY | Directory where to store the submitted files. | /home/user/submissions

The value of the `SUBMIT_COMMAND` variable should use the string `FILE` where the file path of the submitted file is required.

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

