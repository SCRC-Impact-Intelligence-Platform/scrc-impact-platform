from enum import StrEnum


class FormBatchState(StrEnum):
    CREATING = "CREATING"
    READY = "READY"
    SENT = "SENT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PublicationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    UNSURE = "UNSURE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    DISMISSED = "DISMISSED"


class ResourceCriticality(StrEnum):
    CRITICAL = "CRITICAL"
    SIGNIFICANT = "SIGNIFICANT"
    MINOR = "MINOR"


class ResourceType(StrEnum):
    EQUIPMENT = "EQUIPMENT"
    FUNDING = "FUNDING"
    SERVICE = "SERVICE"


class PublicationConfidence(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"
