"""Enumeration types for Okta System Log events."""

from enum import StrEnum


class LogSeverity(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class OutcomeResult(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"
    ALLOW = "ALLOW"
    DENY = "DENY"
    CHALLENGE = "CHALLENGE"
    UNKNOWN = "UNKNOWN"


class TransactionType(StrEnum):
    WEB = "WEB"
    JOB = "JOB"


class AuthenticationProvider(StrEnum):
    OKTA = "OKTA_AUTHENTICATION_PROVIDER"
    ACTIVE_DIRECTORY = "ACTIVE_DIRECTORY"
    LDAP = "LDAP"
    FEDERATION = "FEDERATION"
    SOCIAL = "SOCIAL"
    FACTOR_PROVIDER = "FACTOR_PROVIDER"


class CredentialProvider(StrEnum):
    OKTA = "OKTA_CREDENTIAL_PROVIDER"
    RSA = "RSA"
    SYMANTEC = "SYMANTEC"
    GOOGLE = "GOOGLE"
    DUO = "DUO"
    YUBIKEY = "YUBIKEY"


class CredentialType(StrEnum):
    OTP = "OTP"
    SMS = "SMS"
    PASSWORD = "PASSWORD"
    ASSERTION = "ASSERTION"
    IWA = "IWA"
    EMAIL = "EMAIL"
    OAUTH2 = "OAUTH2"
    JWT = "JWT"
    CERTIFICATE = "CERTIFICATE"
    PRE_SHARED_SYMMETRIC_KEY = "PRE_SHARED_SYMMETRIC_KEY"
    OKTA_CLIENT_SESSION = "OKTA_CLIENT_SESSION"
    DEVICE_UDID = "DEVICE_UDID"
