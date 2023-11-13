class ForbiddenException(Exception):
    def __init__(self, message="Access denied."):
        self.message = message
        super().__init__(self.message)


class CustomError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)