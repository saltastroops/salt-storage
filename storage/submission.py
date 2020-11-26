"""Submit proposal content."""
import asyncio
import os
import pathlib
import subprocess
import threading
import uuid
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
    proposal_filepath = await save_submitted_content(content)
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
        command_string = os.environ["SUBMIT_COMMAND"].replace(
            "FILE", str(proposal.absolute())
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


async def save_submitted_content(content: UploadFile) -> pathlib.Path:
    """
    Save the submitted proposal.

    The path of the generated file is returned.
    """
    await content.seek(0)
    saved_filepath = pathlib.Path(os.environ["SUBMIT_DIRECTORY"]).joinpath(
        str(uuid.uuid4())
    )
    with open(saved_filepath, "wb") as f:
        f.write(cast(bytes, await content.read()))

    return saved_filepath
