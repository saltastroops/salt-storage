"""Submission related database access."""
import enum
from typing import Optional

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
    database: Database, identifier: str, submitter: str, proposal_code: Optional[str]
) -> None:
    """Create a new submission entry in the database."""
    print("PC", proposal_code)
    query = """
INSERT INTO Submission (Identifier, Submitter_Id, ProposalCode_Id, SubmissionStatus_Id,
                        StartedAt)
    VALUES (
        :identifier,
        (SELECT PiptUser_Id FROM PiptUser WHERE Username=:username),
        IF(
           ISNULL(:proposal_code),
           NULL,
           (
               SELECT ProposalCode_Id
               FROM ProposalCode
               WHERE Proposal_Code = :proposal_code
           )
        ),
        (SELECT SubmissionStatus_Id FROM SubmissionStatus
         WHERE SubmissionStatus='In Progress'),
        NOW()
    )
    """
    values = {
        "identifier": identifier,
        "username": submitter,
        "proposal_code": proposal_code,
    }
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
INSERT INTO SubmissionLogEntry (SubmissionLogEntryNumber, Submission_Id, Message,
                                SubmissionMessageType_Id)
    VALUES (
        (
            SELECT COUNT(*) + 1
            FROM SubmissionLogEntry sle
            JOIN Submission s ON sle.Submission_Id = s.Submission_Id
            WHERE s.Identifier = :identifier
        ),
        (SELECT Submission_Id FROM Submission WHERE Identifier=:identifier),
        :message,
        (
            SELECT SubmissionMessageType_Id FROM SubmissionMessageType
            WHERE SubmissionMessageType=:message_type
        )
    )
    """
    values = {
        "identifier": identifier,
        "message": message,
        "message_type": message_type.value,
    }
    await database.execute(query=query, values=values)
