#!/usr/bin/python3
"""Custom exceptions, raised by pyupspack library from time to time.

This module contains the custom exceptions that pyupspack uses from time to time.
Where possible/sensible, pyupspack uses stock exceptions, such as ValueError or
SyntaxError; sometimes, however, it is more appropriate to raise an exception whose
name reflects a unique problem or concern that occurred within the pyupspack library.

Classes:
    ?
    
Todo:
    * Add list of classes

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""


class Error(Exception):
    """Base exception. All other exceptions below are subclasses of this.

    Note:
        Do not raise this. It is boring an uninformative.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Base class for other exceptions'


class InitializationError(Error):
    """Subclass for initialization exceptions
    
    This is a class of the exceptions that occur when the pyupspack
    library is being initialized. Do not raise this. Use it as a
    catchall when 'except'ing (if you must).

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all initialization errors'


class CachingStructureInitializationError(InitializationError):
    """Raised if a cache initialization error occurs in SmartUPSInterface.
    
    When an instance of SmartUPSInterface is initialized, the output of
    the circuit board's serial port is read repeatedly until something
    meaningful is returned or the upper limit of attempts has been reached.
    If nothing meaningful has been returned, this exception is raised.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all caching structure initialization errors'


class CachingStructurePrematureReadError(InitializationError):
    """Raised if a read is attempted before a value has been cached.
    
    When a SelfCachingCall instance is created, one of the things this to happen
    is the reading and caching of a value from the specified subroutine. However,
    if the programmer tries to read the cached value before a value has been
    cached, this exception is raised.
    
    In an ideal world, each SelfCachingCall instance would make a programmer wait
    until a value had been cached and *then* return the value. However, I am too
    lazy to do that. Also, for some reason, I don't like locking up a program. 

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all caching structure premature read errors'


class SmartUPSInitializationError(InitializationError):
    """Cannot find the serial port/USB port associated with the circuit board.
    
    It may be that two serial ports exist or that no port exists at all. In any
    case, identify_serial_device() raises this exception if a unique serial
    port of the circuit board cannot be found. In that case, the programmer may
    wish to specify the serial port when doing this.
    
    Example:
        >>> try:
        >>>     from pyupspack import SmartUPS
        >>> except SmartUPSInitializationError:
        >>>     SmartUPS = SmartUPSInterface(serial_device="/dev/ttyUSB0")

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all smart ups initialization errors'


class ReadError(Error):
    """Class on which ReadSmartUPSError, ReadOnlyError, etc. are based.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all read errors'


class ReadSmartUPSError(ReadError):
    """Raised if the SmartUPS instance fails to read the output of the circuit board.
    
    If the SmartUPS interface fails to read the output of the RPi UPSPack circuit
    board, this exception is raised.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all read-smart-ups errors'


class ReadOnlyError(ReadError):
    """My alternative to AttributeError.
    
    This is raised by pyupspack if the programmer tries to set a read-only
    value. Perhaps I should use AttributeError instead...? QQQ

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all read-only errors --- do not write'


class CachingError(Error):
    """Raised by a SelfCachingCall instance if caching fails.
    
    If an instance of SelfCachingCall tries but fails to cache the output
    of the supplied function, this exception is raised.

    Args:
        msg (str): Human readable string describing the exception.
        code (:obj:`int`, optional): Error code.

    Attributes:
        msg (str): Human readable string describing the exception.
        code (int): Exception error code.

    """

    def __init__(self, message):
        super().__init__(message)
        self.__doc__ = 'Class for all caching errors'

