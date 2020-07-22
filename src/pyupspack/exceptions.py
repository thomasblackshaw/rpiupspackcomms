#!/usr/bin/python3

'''
My exceptions
'''


class Error(Exception):
    """Base class for other exceptions"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Base class for other exceptions'


class InitializationError(Error):
    """Class for all initialization errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all initialization errors'


class CachingStructureInitializationError(InitializationError):
    """Class for all caching structure initialization errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all caching structure initialization errors'


class CachingStructurePrematureReadError(InitializationError):
    """Class for all caching structure premature read errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all caching structure premature read errors'


class SmartUPSInitializationError(InitializationError):
    """Class for all smart ups initialization errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all smart ups initialization errors'


class ReadError(Error):

    """Class for all read errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all read errors'


class ReadSmartUPSError(ReadError):

    """Class for all read-smart-ups errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all read-smart-ups errors'


class ReadOnlyError(ReadError):

    """Class for all read-only errors --- do not write"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all read-only errors --- do not write'


class CachingError(Error):
    """Class for all caching errors"""

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all caching errors'

