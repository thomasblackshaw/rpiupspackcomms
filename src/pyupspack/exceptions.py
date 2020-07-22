#!/usr/bin/python3

'''
My exceptions
'''


class Error(Exception):
    """Base class for other exceptions"""

    def __init__(self, message):
        super().__init__(message)


class InitializationError(Error):
    """Class for all initialization errors"""

    def __init__(self, message):
        super().__init__(message)


class CachingStructureInitializationError(InitializationError):
    """Class for all caching structure initialization errors"""

    def __init__(self, message):
        super().__init__(message)


class CachingStructurePrematureReadError(InitializationError):
    """Class for all caching structure premature read errors"""

    def __init__(self, message):
        super().__init__(message)


class SmartUPSInitializationError(InitializationError):
    """Class for all smart ups initialization errors"""

    def __init__(self, message):
        super().__init__(message)


class ReadError(Error):

    """Class for all read errors"""

    def __init__(self, message):
        super().__init__(message)


class ReadSmartUPSError(ReadError):

    """Class for all read-smart-ups errors"""

    def __init__(self, message):
        super().__init__(message)


class ReadOnlyError(ReadError):

    """Class for all read-only errors --- do not write"""

    def __init__(self, message):
        super().__init__(message)


class CachingError(Error):
    """Class for all caching errors"""

    def __init__(self, message):
        super().__init__(message)
