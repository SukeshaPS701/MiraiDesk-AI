class MiraiDeskException(Exception):
    """
    Base exception for MiraiDesk-AI application errors.
    """

    def __init__(
        self,
        message: str = "An application error occurred."
    ):
        self.message = message
        super().__init__(self.message)


class DatabaseException(MiraiDeskException):
    """
    Exception raised when a database operation fails.
    """

    def __init__(
        self,
        message: str = "A database error occurred."
    ):
        super().__init__(message)