"""Submit proposal content."""

import os
import pathlib
import subprocess
import threading
import uuid
from enum import Enum
from typing import Optional, cast

from fastapi import UploadFile


class MessageType(Enum):
    """Submission message types."""

    ERROR = "Error"
    INFO = "Info"
    WARNING = "Warning"


async def submit(content: UploadFile, proposal_code: Optional[str]) -> str:
    """
    Submit proposal content.

    The function returns an id for the submission, which can be used for subscribing to
    the submission log.
    """
    submission_id = str(uuid.uuid4())
    proposal_filepath = await save_submitted_content(content)
    t = threading.Thread(
        target=execute_submission,
        args=[proposal_filepath, proposal_code, submission_id],
    )
    t.start()
    return submission_id


def execute_submission(
    proposal: pathlib.Path, proposal_code: Optional[str], submission_id: str
) -> None:
    """Execute the submission."""
    command = os.environ["SUBMIT_COMMAND"].replace("FILE", str(proposal.absolute()))
    subprocess.run(command.split(" "))
    # if cp.returncode:
    #     message_type = MessageType.ERROR
    #     message = "Submission failed."
    # else:
    #     message_type = MessageType.INFO
    #     message = "Submission successful."


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
