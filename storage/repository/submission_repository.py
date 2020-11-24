"""Submission related database access."""
import enum

from databases import Database


class SubmissionStatus(enum.Enum):
    """A submission status."""

    FAILED = "Failed"
    IN_PROGRESS = "In Progress"
    SUCCESSFUL = "Successful"


class SubmissionMessageType(enum.Enum):
    """A submission message type."""

    ERROR = "Error"
    INFO = "Info"
    WARNING = "Warning"


async def create_submission(
    database: Database, identifier: str, submitter: str
) -> None:
    """Create a new submission entry in the database."""
    query = """
INSERT INTO Submission (Identifier, Submitter_Id, SubmissionStatus_Id, StartedAt)
    VALUES (
        :identifier,
        (SELECT PiptUser_Id FROM PiptUser WHERE Username=:username),
        (SELECT SubmissionStatus_Id FROM SubmissionStatus
         WHERE SubmissionStatus='In Progress'),
        NOW()
    )
    """
    values = {"identifier": identifier, "username": submitter}
    await database.execute(query=query, values=values)


async def update_submission(
    database: Database, identifier: str, status: SubmissionStatus
) -> None:
    """Update a submission entry in the database."""
    query = """
UPDATE Submission SET
     SubmissionStatus_Id=(SELECT SubmissionStatus_Id FROM SubmissionStatus
                          WHERE SubmissionStatus=:status),
     FinishedAt=NOW()
WHERE Identifier=:identifier
"""
    values = {"identifier": identifier, "status": status.value}
    await database.execute(query=query, values=values)


async def log_submission_message(
    database: Database,
    identifier: str,
    message: str,
    message_type: SubmissionMessageType,
) -> None:
    """Log a submission message in the database."""
    query = """
INSERT INTO SubmissionLogEntry (Submission_Id, Message, SubmissionMessageType_Id)
    VALUES (
        (SELECT Submission_Id FROM Submission WHERE Identifier=:identifier),
        :message,
        (SELECT SubmissionMessageType_Id FROM SubmissionMessageType
         WHERE SubmissionMessageType=:message_type)
    )
    """
    values = {
        "identifier": identifier,
        "message": message,
        "message_type": message_type.value,
    }
    await database.execute(query=query, values=values)
