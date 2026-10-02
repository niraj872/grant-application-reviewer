from typing import Literal, Optional
from pydantic import BaseModel, Field
Cat = Literal["eligibility", "submission", "documentation", "project", "budget", "timeline", "other"]
Status = Literal["satisfied", "weak", "missing", "ambiguous", "unsupported"]
class Source(BaseModel):
    document: str; page: Optional[int] = None; section: Optional[str] = None
class ReqOut(BaseModel):
    requirement_text: str = Field(min_length=3); category: Cat; importance: Literal["mandatory", "recommended"]
    ambiguous: bool = False; source: Source
class ReqList(BaseModel): requirements: list[ReqOut]
class MapOut(BaseModel):
    requirement_id: int; application_evidence: str = ""; application_source: Optional[Source] = None
    status: Status; confidence: float = Field(ge=0, le=1); reason: str = ""
class MapList(BaseModel): mappings: list[MapOut]
class ClaimOut(BaseModel): claim: str; source: Source; note: str = "Not supported by supplied evidence"
class ClaimList(BaseModel): claims: list[ClaimOut]
class QOut(BaseModel): question: str; requirement_id: Optional[int] = None; claim_index: Optional[int] = None
class QList(BaseModel): questions: list[QOut]
class AssessmentIn(BaseModel): guideline_version_id: int; application_version_id: int
class ReviewIn(BaseModel):
    decision: Literal["confirm", "correct", "reject"]
    corrected_status: Optional[Status] = None; corrected_evidence: Optional[str] = None; note: str = ""
class DocStateIn(BaseModel): state: Literal["provided", "missing", "not_applicable"]
