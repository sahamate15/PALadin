class PaladinError(Exception):
    """Expected user-facing PALadin error."""


class DependencyError(PaladinError):
    pass


class ProbeError(PaladinError):
    pass


class ProcessingError(PaladinError):
    pass


class UnsafeSubtitleError(PaladinError):
    pass
