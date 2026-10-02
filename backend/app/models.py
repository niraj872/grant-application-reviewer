from datetime import datetime, timezone
from sqlalchemy import ForeignKey, JSON, String, Text, Boolean, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column as col, relationship
def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class Guideline(Base):
    __tablename__ = "guidelines"
    id: Mapped[int] = col(primary_key=True); name: Mapped[str] = col(String(255))
    versions = relationship("GuidelineVersion", back_populates="guideline", order_by="GuidelineVersion.version")
class GuidelineVersion(Base):
    __tablename__ = "guideline_versions"
    id: Mapped[int] = col(primary_key=True); guideline_id: Mapped[int] = col(ForeignKey("guidelines.id"))
    version: Mapped[int]; filename: Mapped[str] = col(String(255)); text: Mapped[str] = col(Text)
    pages: Mapped[list] = col(JSON); content_hash: Mapped[str] = col(String(64)); uploaded_at: Mapped[datetime] = col(DateTime, default=now)
    guideline = relationship("Guideline", back_populates="versions")
    requirements = relationship("Requirement", back_populates="guideline_version")
class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = col(primary_key=True); name: Mapped[str] = col(String(255))
    versions = relationship("ApplicationVersion", back_populates="application", order_by="ApplicationVersion.version")
class ApplicationVersion(Base):
    __tablename__ = "application_versions"
    id: Mapped[int] = col(primary_key=True); application_id: Mapped[int] = col(ForeignKey("applications.id"))
    version: Mapped[int]; filename: Mapped[str] = col(String(255)); text: Mapped[str] = col(Text)
    pages: Mapped[list] = col(JSON); content_hash: Mapped[str] = col(String(64)); uploaded_at: Mapped[datetime] = col(DateTime, default=now)
    application = relationship("Application", back_populates="versions")
    supporting_documents = relationship("SupportingDocument", back_populates="application_version")
class SupportingDocument(Base):
    __tablename__ = "supporting_documents"
    id: Mapped[int] = col(primary_key=True); application_version_id: Mapped[int] = col(ForeignKey("application_versions.id"))
    name: Mapped[str] = col(String(255)); doc_type: Mapped[str] = col(String(100), default="")
    required: Mapped[bool] = col(Boolean, default=True)
    state: Mapped[str] = col(String(20), default="missing")  # provided | missing | not_applicable
    description: Mapped[str] = col(Text, default="")
    application_version = relationship("ApplicationVersion", back_populates="supporting_documents")
class Requirement(Base):
    __tablename__ = "requirements"
    id: Mapped[int] = col(primary_key=True); guideline_version_id: Mapped[int] = col(ForeignKey("guideline_versions.id"))
    text: Mapped[str] = col(Text); category: Mapped[str] = col(String(30)); importance: Mapped[str] = col(String(20))
    ambiguous: Mapped[bool] = col(Boolean, default=False); source: Mapped[dict] = col(JSON)
    guideline_version = relationship("GuidelineVersion", back_populates="requirements")
class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = col(primary_key=True)
    guideline_version_id: Mapped[int] = col(ForeignKey("guideline_versions.id"))
    application_version_id: Mapped[int] = col(ForeignKey("application_versions.id"))
    created_at: Mapped[datetime] = col(DateTime, default=now)
    guideline_version = relationship("GuidelineVersion"); application_version = relationship("ApplicationVersion")
    mappings = relationship("RequirementMapping", back_populates="assessment")
    claims = relationship("UnsupportedClaim"); questions = relationship("ClarificationQuestion")
class RequirementMapping(Base):
    __tablename__ = "requirement_mappings"
    id: Mapped[int] = col(primary_key=True); assessment_id: Mapped[int] = col(ForeignKey("assessments.id"))
    requirement_id: Mapped[int] = col(ForeignKey("requirements.id"))
    evidence: Mapped[str] = col(Text, default=""); source: Mapped[dict | None] = col(JSON, nullable=True)
    status: Mapped[str] = col(String(20)); confidence: Mapped[float] = col(Float, default=0.0); reason: Mapped[str] = col(Text, default="")
    assessment = relationship("Assessment", back_populates="mappings"); requirement = relationship("Requirement")
    decisions = relationship("ReviewerDecision", order_by="ReviewerDecision.id")
class ReviewerDecision(Base):
    __tablename__ = "reviewer_decisions"
    id: Mapped[int] = col(primary_key=True); mapping_id: Mapped[int] = col(ForeignKey("requirement_mappings.id"))
    decision: Mapped[str] = col(String(10))  # confirm | correct | reject
    corrected_status: Mapped[str | None] = col(String(20), nullable=True); corrected_evidence: Mapped[str | None] = col(Text, nullable=True)
    note: Mapped[str] = col(Text, default=""); created_at: Mapped[datetime] = col(DateTime, default=now)
class UnsupportedClaim(Base):
    __tablename__ = "unsupported_claims"
    id: Mapped[int] = col(primary_key=True); assessment_id: Mapped[int] = col(ForeignKey("assessments.id"))
    claim: Mapped[str] = col(Text); source: Mapped[dict] = col(JSON); note: Mapped[str] = col(Text, default="")
class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"
    id: Mapped[int] = col(primary_key=True); assessment_id: Mapped[int] = col(ForeignKey("assessments.id"))
    question: Mapped[str] = col(Text); requirement_id: Mapped[int | None] = col(ForeignKey("requirements.id"), nullable=True)
    claim_id: Mapped[int | None] = col(ForeignKey("unsupported_claims.id"), nullable=True)
