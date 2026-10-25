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
    DISMISSED = "DISMISSED"


class ResourceType(StrEnum):
    EQUIPMENT = "EQUIPMENT"
    FUNDING = "FUNDING"
    SERVICE = "SERVICE"