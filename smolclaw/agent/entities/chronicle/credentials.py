"""Credential and login result entities for Chronicle integration."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SaaSCredentials(BaseModel):
    saas_name: str
    username: str
    password: str
    totp_seed: str | None = None


class LoginResult(BaseModel):
    success: bool
    landed_url: str
    mfa_used: bool = False
    error: str | None = None


class BitwardenURI(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uri: str | None = None
    match: int | None = None


class BitwardenLogin(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str | None = None
    uris: list[BitwardenURI] | None = None


class BitwardenItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    login: BitwardenLogin | None = None
    organization_id: str | None = Field(default=None, alias="organizationId")
