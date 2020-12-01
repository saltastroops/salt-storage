"""Submit proposal content."""
import asyncio
import os
import pathlib
import re
import subprocess
import threading
import uuid
from datetime import datetime
from typing import Optional, cast

import databases
from dotenv import load_dotenv
from fastapi import UploadFile

from storage.repository.submission_repository import (
    SubmissionMessageType,
    SubmissionStatus,
    create_submission,
    log_submission_message,
    update_submission,
)

load_dotenv()
DATABASE_DSN = os.environ["DATABASE_URL"]


async def submit(
    content: UploadFile, submitter: str, proposal_code: Optional[str]
) -> str:
    """
    Submit proposal content.

    The function returns an identifier for the submission, which can be used for
    subscribing to the submission progress.
    """
    submission_identifier = str(uuid.uuid4())
    async with databases.Database(DATABASE_DSN) as database:
        await create_submission(
            database=database,
            identifier=submission_identifier,
            submitter=submitter,
            proposal_code=proposal_code,
        )
    proposal_filepath = await save_submitted_content(content, submission_identifier)
    t = threading.Thread(
        target=call_execute_submission,
        args=[proposal_filepath, proposal_code, submission_identifier, submitter],
    )
    t.start()
    return submission_identifier


def call_execute_submission(
    proposal: pathlib.Path,
    proposal_code: Optional[str],
    submission_identifier: str,
    submitter: str,
) -> None:
    """Call the execute_submission in a new event loop."""
    asyncio.run(
        execute_submission(
            proposal=proposal,
            proposal_code=proposal_code,
            submission_identifier=submission_identifier,
            submitter=submitter,
        )
    )


async def execute_submission(
    proposal: pathlib.Path,
    proposal_code: Optional[str],
    submission_identifier: str,
    submitter: str,
) -> None:
    """Execute the submission."""
    async with databases.Database(DATABASE_DSN) as database:
        await log_submission_message(
            database=database,
            identifier=submission_identifier,
            message="Submission started.",
            message_type=SubmissionMessageType.INFO,
        )
        command_string = submission_command(
            content=proposal.absolute(),
            submitter=submitter,
            proposal_code=proposal_code,
        )
        command = command_string.split(" ")
        if proposal_code:
            command.insert(-1, "-proposalCode")
            command.insert(-1, proposal_code)
        await log_submission_message(
            database=database,
            identifier=submission_identifier,
            message="Inserting proposal into the database",
            message_type=SubmissionMessageType.INFO,
        )
        cp = subprocess.run(command)
        if cp.returncode:
            submission_status = SubmissionStatus.FAILED
            message_type = SubmissionMessageType.ERROR
            message = "Submission failed."
        else:
            submission_status = SubmissionStatus.SUCCESSFUL
            message_type = SubmissionMessageType.INFO
            message = "Submission successful."
        await log_submission_message(
            database=database,
            identifier=submission_identifier,
            message=message,
            message_type=message_type,
        )
        await update_submission(
            database=database,
            identifier=submission_identifier,
            status=submission_status,
        )


def submission_command(
    content: pathlib.Path, submitter: str, proposal_code: Optional[str]
) -> str:
    """Generate the command for submitting the proposal."""
    log_name = mapping_log_name(proposal_code)
    command = f"""
    java -Xms85m -Xmx1024m
         -jar {os.environ['WEB_MANAGER_DIR']}/java/MappingService.jar
         -access {os.environ['WEB_MANAGER_DIR']}/java/DatabaseAccess.conf
         -log {os.environ['WEB_MANAGER_DIR']}/replicate/mapper_logs/{log_name}
         -user {submitter}
         -convert {os.environ['CONVERT_COMMAND']}
         -save {os.environ['WEB_MANAGER_DIR']}/replicate/proposals
         -file {content}
         {('-proposalCode ' + proposal_code) if proposal_code else ""}
         -piptDir {os.environ['PIPT_DIR']}
         -server {os.environ['WEB_MANAGER_URL']}
         -ephemerisUrl {os.environ['EPHEMERIS_URL']}
         -findingChartGenerationScript {os.environ['FINDER_CHART_TOOL']}
         -python python
         -sentryDSN {os.environ['SENTRY_DSN']}
         {os.environ['MAPPING_TOOL_API_KEY']}
    """
    command = re.sub(r"\s+", " ", command)
    command = command.replace("\n", "").strip()
    return command


async def save_submitted_content(
    content: UploadFile, submission_identifier: str
) -> pathlib.Path:
    """
    Save the submitted proposal.

    The path of the generated file is returned.
    """
    await content.seek(0)
    saved_filepath = (
        pathlib.Path(os.environ["WEB_MANAGER_DIR"])
        .joinpath("replicate")
        .joinpath("submissions")
        .joinpath(submission_identifier)
    )
    with open(saved_filepath, "wb") as f:
        f.write(cast(bytes, await content.read()))

    return saved_filepath


def mapping_log_name(proposal_code: Optional[str]) -> str:
    """Generate the name for the log file."""
    name = f"{proposal_code}-" if proposal_code else ""
    return name + datetime.now().isoformat()
