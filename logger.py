# Logger to UI

class Logger:
    def __init__(self, ui):
        self.ui = ui

    def log(self, message):
        self.ui.log(message)

    def log_error(self, message):
        self.ui.log_error(message)

    def log_warning(self, message):
        self.ui.log_warning(message)

    def log_info(self, message):
        self.ui.log_info(message)

    def log_debug(self, message):
        self.ui.log_debug(message)
