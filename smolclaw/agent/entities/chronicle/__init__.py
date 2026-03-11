"""Chronicle entity models for SSPM domain."""

from .agent_config import (
    Agent,
    AgentStatus,
    ConnectionStatus,
    ScanFrequency,
)
from .analysis import (
    AnalysisMetadata,
    ComplianceStatus,
    FrameworkAnalysisResult,
    FrameworkControl,
    FrameworkMappings,
    RiskLevel,
    RiskSummary,
    SettingAnalysis,
)
from .app_drift import (
    AppDrift,
    ChildAppsAddedChangeDetails,
    ChildAppsRemovedChangeDetails,
    NewAppChangeDetails,
    PermissionsAddedChangeDetails,
    PermissionsRemovedChangeDetails,
    RemovedAppChangeDetails,
)
from .app_inventory import (
    AppInventoryResult,
    AppInventoryScanResult,
    AppWithChanges,
    InstalledApp,
)
from .credentials import (
    BitwardenItem,
    BitwardenLogin,
    BitwardenURI,
    LoginResult,
    SaaSCredentials,
)
from .extraction_schema import (
    BaselineSetting,
    ExtractionSchema,
)
from .harvest import (
    HarvestAction,
    HarvestResult,
    InteractionType,
    SettingsNode,
)
from .navigation import (
    ActionType,
    ExplorationResult,
    FallbackContext,
    NavigationMap,
    NavigationResult,
    NavStep,
    ScreenshotCapture,
    StepExecutionResult,
    VerificationResult,
)
from .pipeline import (
    JobPhase,
    JobSpec,
    JobStatus,
    PipelineJob,
    StagePhase,
    StageStatus,
    StageType,
)
from .saas import (
    ExplorationDraft,
    LoginSelectors,
    MFAConfig,
    OnboardingStatus,
    PreLoginSelectors,
    SaaSApp,
    SaaSConfig,
    SAAS_CONFIGS,
    SSOConfig,
    VerificationStatus,
    get_saas_config,
)
from .schedule_run import (
    CreateScheduleRunRequest,
    ScheduleRun,
    ScheduleRunStatus,
)
from .settings import (
    ElementType,
    ExtractedSetting,
    ExtractedSettingsPage,
    ExtractionResult,
)
from .vault import (
    Vault,
    VaultCredential,
    VaultCredentialRef,
    VaultStatus,
    VaultTestResult,
    VaultType,
)

__all__ = [
    # agent_config
    "Agent",
    "AgentStatus",
    "ConnectionStatus",
    "ScanFrequency",
    # analysis
    "AnalysisMetadata",
    "ComplianceStatus",
    "FrameworkAnalysisResult",
    "FrameworkControl",
    "FrameworkMappings",
    "RiskLevel",
    "RiskSummary",
    "SettingAnalysis",
    # app_drift
    "AppDrift",
    "ChildAppsAddedChangeDetails",
    "ChildAppsRemovedChangeDetails",
    "NewAppChangeDetails",
    "PermissionsAddedChangeDetails",
    "PermissionsRemovedChangeDetails",
    "RemovedAppChangeDetails",
    # app_inventory
    "AppInventoryResult",
    "AppInventoryScanResult",
    "AppWithChanges",
    "InstalledApp",
    # credentials
    "BitwardenItem",
    "BitwardenLogin",
    "BitwardenURI",
    "LoginResult",
    "SaaSCredentials",
    # extraction_schema
    "BaselineSetting",
    "ExtractionSchema",
    # harvest
    "HarvestAction",
    "HarvestResult",
    "InteractionType",
    "SettingsNode",
    # navigation
    "ActionType",
    "ExplorationResult",
    "FallbackContext",
    "NavigationMap",
    "NavigationResult",
    "NavStep",
    "ScreenshotCapture",
    "StepExecutionResult",
    "VerificationResult",
    # pipeline
    "JobPhase",
    "JobSpec",
    "JobStatus",
    "PipelineJob",
    "StagePhase",
    "StageStatus",
    "StageType",
    # saas
    "ExplorationDraft",
    "LoginSelectors",
    "MFAConfig",
    "OnboardingStatus",
    "PreLoginSelectors",
    "SaaSApp",
    "SaaSConfig",
    "SAAS_CONFIGS",
    "SSOConfig",
    "VerificationStatus",
    "get_saas_config",
    # schedule_run
    "CreateScheduleRunRequest",
    "ScheduleRun",
    "ScheduleRunStatus",
    # settings
    "ElementType",
    "ExtractedSetting",
    "ExtractedSettingsPage",
    "ExtractionResult",
    # vault
    "Vault",
    "VaultCredential",
    "VaultCredentialRef",
    "VaultStatus",
    "VaultTestResult",
    "VaultType",
]
