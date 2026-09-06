"""Domain errors.

Every one of these maps to exactly one HTTP status in app/api/errors.py. The
point is that services raise meaning ("the provider returned something that
isn't a scorecard") rather than transport ("500"), and nothing leaks a raw
provider message to the client.
"""


class DomainError(Exception):
    """Base for everything this application raises deliberately."""


class ConfigurationError(DomainError):
    """A required setting is missing or contradictory. Raised at startup."""


class NotFoundError(DomainError):
    """A requested entity does not exist."""


class ProviderError(DomainError):
    """An upstream model provider failed or was unreachable."""


class InvalidProviderOutput(ProviderError):
    """
    The provider replied, but the reply did not satisfy the schema.

    This is its own type because the old code swallowed exactly this case and
    returned an empty scorecard, so a malformed response looked to the user
    like an ad that scored zero on everything.
    """


class KnowledgeStoreUnavailable(DomainError):
    """The vector store is not ready to serve retrievals."""
