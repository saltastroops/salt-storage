"""The server."""
from typing import Any, Callable, Dict, List, Optional, cast

import dotenv
from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, validator

from storage import auth, submission

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


@app.middleware("http")
async def enforce_admin_user(request: Request, call_next: Callable) -> Response:
    """Only allow requests if a token with Admin scope is supplied."""
    if "Authorization" not in request.headers:
        return PlainTextResponse("Authorization header missing.", status_code=401)

    authorization_header = request.headers["Authorization"]
    if not authorization_header.startswith("Bearer "):
        return PlainTextResponse(
            "Invalid Authorization header value. The header "
            "value must have the format Bearer <token>.",
            status_code=401,
        )

    token = request.headers["Authorization"][7:]  # length of "Bearer " is 7
    try:
        payload = auth.parse_token(token, refetch_public_key_on_failure=True)
    except Exception:
        return PlainTextResponse("Invalid or expired token.", status_code=401)

    if "Admin" not in cast(List, payload.get("roles", [])):
        return PlainTextResponse("", 403)

    return await call_next(request)


@app.post(
    "/proposal/submit",
    response_model=SubmissionResponseModel,
    response_model_exclude_none=True,
)
async def submit_proposal(
    proposal: UploadFile = File(...),
    submitter: str = Form(...),
    proposal_code: str = Form(None),
) -> Dict[str, str]:
    """Submit a proposal."""
    try:
        submission_id = await submission.submit(
            content=proposal, submitter=submitter, proposal_code=proposal_code
        )
        return {"submission_id": submission_id}
    except Exception as e:
        return {"error": str(e)}
