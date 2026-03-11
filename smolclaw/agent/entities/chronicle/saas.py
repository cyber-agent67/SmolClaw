"""SaaS application and configuration entities for Chronicle integration."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OnboardingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# SaaS application models
# ---------------------------------------------------------------------------

class SaaSApp(BaseModel):
    saas_id: str
    name: str
    landing_url_template: str
    credential_key: str
    login_success_url_patterns: list[str] = []
    pre_login_action: str | None = None
    notes: str | None = None
    is_enabled: bool = True
    onboarding_status: OnboardingStatus = OnboardingStatus.PENDING
    supports_vision_agent: bool = False
    supports_connector: bool = False
    is_supported: bool = False
    color: str | None = None
    category: str | None = None
    hostname: str | None = None
    map_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExplorationDraft(BaseModel):
    uid: str
    job_uid: str
    saas_id: str
    map_name: str
    start_url: str
    steps: list[dict] = []
    step_count: int = 0
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_job_uid: str | None = None
    verified_at: datetime | None = None
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Configuration models
# ---------------------------------------------------------------------------

class LoginSelectors(BaseModel):
    login_domain: str
    username: list[str]
    password: list[str]
    submit: list[str]


class PreLoginSelectors(BaseModel):
    input_selector: str
    input_value_template: str
    submit_selector: str


class MFAConfig(BaseModel):
    switch_method_selectors: list[str] = []
    select_totp_selectors: list[str] = []
    totp_input_selectors: list[str] = []
    fastpass_selectors: list[str] = []
    switch_method_llm_fallback: str | None = None


class SSOConfig(BaseModel):
    idp_type: str
    idp_domain: str
    idp_login_url_pattern: str | None = None
    pre_sso_action: str | None = None
    idp_login_selectors: LoginSelectors | None = None
    idp_mfa_config: MFAConfig | None = None
    idp_credential_key: str | None = None
    wait_for_redirect_timeout: float = 10.0


class SaaSConfig(BaseModel):
    saas_id: str
    name: str
    landing_url_template: str
    credential_key: str
    login_success_url_patterns: list[str] = []
    pre_login_action: str | None = None
    pre_login_selectors: PreLoginSelectors | None = None
    notes: str | None = None
    login_selectors: LoginSelectors | None = None
    mfa_config: MFAConfig | None = None
    post_login_action: str | None = None
    required_extension_url: str | None = None
    sso_config: SSOConfig | None = None

    def get_landing_url(self, workspace_id: str) -> str:
        return self.landing_url_template.format(workspace_id=workspace_id)


# ---------------------------------------------------------------------------
# Predefined SaaS configurations
# ---------------------------------------------------------------------------

SAAS_CONFIGS: dict[str, SaaSConfig] = {
    "slack": SaaSConfig(
        saas_id="slack",
        name="Slack",
        landing_url_template="https://app.slack.com/client/{workspace_id}",
        credential_key="slack",
        login_success_url_patterns=[
            "app.slack.com/client",
        ],
        login_selectors=LoginSelectors(
            login_domain="slack.com",
            username=[
                'input[data-qa="login_email"]',
                'input[type="email"]',
            ],
            password=[
                'input[data-qa="login_password"]',
                'input[type="password"]',
            ],
            submit=[
                'button[data-qa="login_signin_button"]',
                'button[type="submit"]',
            ],
        ),
        mfa_config=MFAConfig(
            switch_method_selectors=[],
            select_totp_selectors=[],
            totp_input_selectors=[
                'input[data-qa="confirmation_code_input"]',
                'input[placeholder="Enter confirmation code"]',
            ],
            fastpass_selectors=[],
        ),
    ),
    "github": SaaSConfig(
        saas_id="github",
        name="GitHub",
        landing_url_template="https://github.com/{workspace_id}",
        credential_key="github",
        login_success_url_patterns=[
            "github.com",
        ],
        login_selectors=LoginSelectors(
            login_domain="github.com",
            username=[
                'input[name="login"]',
                "#login_field",
            ],
            password=[
                'input[name="password"]',
                "#password",
            ],
            submit=[
                'input[name="commit"]',
                'input[type="submit"]',
            ],
        ),
        mfa_config=MFAConfig(
            switch_method_selectors=[],
            select_totp_selectors=[
                'a[href*="totp"]',
            ],
            totp_input_selectors=[
                'input[name="app_otp"]',
                "#totp",
            ],
            fastpass_selectors=[],
        ),
    ),
    "google_workspace": SaaSConfig(
        saas_id="google_workspace",
        name="Google Workspace",
        landing_url_template="https://workspace.google.com/dashboard",
        credential_key="google_workspace",
        login_success_url_patterns=[
            "myaccount.google.com",
            "workspace.google.com",
            "mail.google.com",
        ],
        login_selectors=LoginSelectors(
            login_domain="accounts.google.com",
            username=[
                'input[type="email"]',
                "#identifierId",
            ],
            password=[
                'input[type="password"]',
                'input[name="Passwd"]',
            ],
            submit=[
                "#identifierNext button",
                "#passwordNext button",
            ],
        ),
        mfa_config=MFAConfig(
            switch_method_selectors=[
                'div[data-challengetype="6"]',
            ],
            select_totp_selectors=[
                'div[data-challengetype="6"]',
            ],
            totp_input_selectors=[
                'input[name="totpPin"]',
                "#totpPin",
            ],
            fastpass_selectors=[],
        ),
    ),
    "microsoft_365": SaaSConfig(
        saas_id="microsoft_365",
        name="Microsoft 365",
        landing_url_template="https://www.office.com/?auth=2",
        credential_key="microsoft_365",
        login_success_url_patterns=[
            "office.com",
            "microsoft365.com",
            "microsoftonline.com",
        ],
        login_selectors=LoginSelectors(
            login_domain="login.microsoftonline.com",
            username=[
                'input[type="email"]',
                'input[name="loginfmt"]',
            ],
            password=[
                'input[type="password"]',
                'input[name="passwd"]',
            ],
            submit=[
                'input[type="submit"]',
                "#idSIButton9",
            ],
        ),
        mfa_config=MFAConfig(
            switch_method_selectors=[
                "#signInAnotherWay",
            ],
            select_totp_selectors=[
                'div[data-value="PhoneAppOTP"]',
            ],
            totp_input_selectors=[
                'input[name="otc"]',
                "#idTxtBx_SAOTC_OTC",
            ],
            fastpass_selectors=[],
        ),
    ),
    "okta": SaaSConfig(
        saas_id="okta",
        name="Okta",
        landing_url_template="https://{workspace_id}.okta.com",
        credential_key="okta",
        login_success_url_patterns=[
            "okta.com/app/UserHome",
        ],
        login_selectors=LoginSelectors(
            login_domain="okta.com",
            username=[
                'input[name="identifier"]',
                'input[name="username"]',
                "#okta-signin-username",
            ],
            password=[
                'input[name="credentials.passcode"]',
                'input[name="password"]',
                "#okta-signin-password",
            ],
            submit=[
                'input[type="submit"]',
                "#okta-signin-submit",
            ],
        ),
        mfa_config=MFAConfig(
            switch_method_selectors=[
                'a[data-se="switchFactorLink"]',
            ],
            select_totp_selectors=[
                'a[data-se="google_otp-factor"]',
                'a[data-se="okta_otp-factor"]',
            ],
            totp_input_selectors=[
                'input[name="credentials.passcode"]',
                'input[name="answer"]',
            ],
            fastpass_selectors=[
                'a[data-se="okta_verify-push-factor"]',
                '[data-se="fastpass-button"]',
            ],
            switch_method_llm_fallback="Click on the option to verify with a code or authenticator app instead of push notification",
        ),
    ),
}


def get_saas_config(saas_id: str) -> Optional[SaaSConfig]:
    """Return the predefined SaaSConfig for the given saas_id, or None."""
    return SAAS_CONFIGS.get(saas_id)
