class CrawlError(RuntimeError):
    """Base error with a stable category for reports and resume logic."""

    category = "CRAWL_ERROR"


class AuthRequired(CrawlError):
    category = "AUTH_REQUIRED"


class RateLimited(CrawlError):
    category = "RATE_LIMITED"


class AntiAutomation(CrawlError):
    category = "ANTI_AUTOMATION"


class RecordNotFound(CrawlError):
    category = "RECORD_NOT_FOUND"


class SchemaChanged(CrawlError):
    category = "SCHEMA_CHANGED"


class NetworkError(CrawlError):
    category = "NETWORK_ERROR"
