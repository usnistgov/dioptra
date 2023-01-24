import enum


class IssueSeverity(enum.Enum):
    ERROR = enum.auto()
    WARNING = enum.auto()


class IssueType(enum.Enum):
    SYNTAX = enum.auto()
    SCHEMA = enum.auto()
    SEMANTIC = enum.auto()
    TYPE = enum.auto()


class ValidationIssue:
    """
    Represents a validation "issue", including errors, warnings, etc.
    """

    def __init__(self, type_: IssueType, severity: IssueSeverity, message: str) -> None:
        self.type = type_
        self.severity = severity
        self.message = message

    def __repr__(self) -> str:
        value = "ValidationIssue({},{},{})".format(
            repr(self.type), repr(self.severity), repr(self.message)
        )

        return value

    def __str__(self) -> str:
        value = "{}.{}: {}".format(
            self.type.name.lower(), self.severity.name.lower(), self.message
        )

        return value
