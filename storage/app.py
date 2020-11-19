"""The server."""
from typing import Any, Dict, Optional

import dotenv
from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel, validator

from storage import submission

dotenv.load_dotenv()

app = FastAPI()


class SubmissionResponseModel(BaseModel):
    """Response model for a successful submission request."""

    submission_id: Optional[str]
    error: Optional[str]

    @validator("error")
    def either_submission_id_or_error(cls: Any, v: str, values: Dict[str, Any]) -> str:
        """Enforce that there is only a submission id or an error, not both."""
        if values.get("submission_id") is not None:
            raise ValueError(
                "The submission_id and error field are mutually exclusive."
            )
        return v


@app.post(
    "/proposal/submit",
    response_model=SubmissionResponseModel,
    response_model_exclude_none=True,
)
async def submit_proposal(
    proposal: UploadFile = File(...), proposal_code: str = Form(None)
) -> Dict[str, str]:
    """Submit a proposal."""
    try:
        submission_id = await submission.submit(proposal, proposal_code)
        return {"submission_id": submission_id}
    except Exception:
        return {"error": "The proposal submission has failed."}
