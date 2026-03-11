"""Framework analysis entities for security compliance evaluation."""
from datetime import UTC, datetime
from enum import Enum
from pydantic import BaseModel, Field, computed_field


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    POSITIVE = "positive"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"


class FrameworkControl(BaseModel):
    control: str
    name: str
    compliance_status: ComplianceStatus
    description: str | None = None


class FrameworkMappings(BaseModel):
    nist_800_53: list[FrameworkControl] = Field(default_factory=list)
    nist_csf: list[FrameworkControl] = Field(default_factory=list)
    soc_2: list[FrameworkControl] = Field(default_factory=list)
    cis_controls: list[FrameworkControl] = Field(default_factory=list)
    iso_27001: list[FrameworkControl] = Field(default_factory=list)

    @computed_field
    @property
    def has_mappings(self) -> bool:
        return bool(
            self.nist_800_53 or self.nist_csf or self.soc_2
            or self.cis_controls or self.iso_27001
        )


class SettingAnalysis(BaseModel):
    setting_id: str
    label: str
    current_value: str
    section: str | None = None
    is_security_relevant: bool
    semantic_description: str
    risk_level: RiskLevel | None = None
    security_impact: str | None = None
    framework_mappings: FrameworkMappings = Field(default_factory=FrameworkMappings)
    recommendation: str | None = None
    recommended_value: str | None = None
    regulatory_implications: list[str] = Field(default_factory=list)


class RiskSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    positive_controls: int = 0
    non_security: int = 0

    @computed_field
    @property
    def total_security_relevant(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.positive_controls

    @computed_field
    @property
    def total(self) -> int:
        return self.total_security_relevant + self.non_security


class AnalysisMetadata(BaseModel):
    scan_timestamp: datetime
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_settings_analyzed: int
    security_relevant_count: int = 0
    frameworks_applied: list[str] = Field(
        default_factory=lambda: ["NIST CSF", "NIST 800-53", "SOC 2", "CIS Controls", "ISO 27001"]
    )
    overall_risk_summary: RiskSummary = Field(default_factory=RiskSummary)
    model_used: str


class FrameworkAnalysisResult(BaseModel):
    run_id: str
    saas_id: str
    workspace_id: str | None = None
    job_uid: str | None = None
    analysis_metadata: AnalysisMetadata
    settings_analysis: list[SettingAnalysis] = Field(default_factory=list)
    success: bool = True
    error: str | None = None

    @computed_field
    @property
    def security_settings(self) -> list[SettingAnalysis]:
        return [s for s in self.settings_analysis if s.is_security_relevant]

    @computed_field
    @property
    def non_security_settings(self) -> list[SettingAnalysis]:
        return [s for s in self.settings_analysis if not s.is_security_relevant]
