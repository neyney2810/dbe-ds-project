import os
from colorama import Fore, Style
import logging
from colorama import just_fix_windows_console
from termcolor import colored


# Logger to UI

class Logger:
    def __init__(self):
        # use Colorama to make Termcolor work on Windows too
        just_fix_windows_console()

        logging.basicConfig(level=logging.INFO)
        client_logger = logging.getLogger('client')
        client_logger.setLevel(logging.INFO)
        self.client_color = os.getenv("CLIENT_COLOR", "green")
        formatter = logging.Formatter(
            f"{Fore}{self.client_color}client: %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        client_logger.addHandler(console_handler)
        self._client_logger = client_logger

        broadcast_logger = logging.getLogger('broadcast')
        broadcast_logger.setLevel(logging.INFO)
        self.broadcast_color = os.getenv("BROADCAST_COLOR", "yellow")
        formatter = logging.Formatter(
            f"{Fore}{self.broadcast_color}broadcast: %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        broadcast_logger.addHandler(console_handler)
        self._broadcast_logger = broadcast_logger

        replica_logger = logging.getLogger('replica')
        replica_logger.setLevel(logging.INFO)
        self.replica_color = os.getenv("REPLICA_COLOR", "cyan")
        formatter = logging.Formatter(
            f"{Fore}{self.replica_color}replica: %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._replica_logger = replica_logger

    def log_client(self, message):
        self._client_logger.info(message)
        print(colored(f"CLIENT: {message}", self.client_color))

    def log_broadcast(self, message):
        self._broadcast_logger.info(message)
        print(colored(f"BROADCAST: {message}", self.broadcast_color))

    def log_replica(self, message):
        self._replica_logger.info(message)
        print(colored(f"REPLICA: {message}", self.replica_color))

    def log_sys(self, message):
        print(colored(f"SYSTEM: {message}", "magenta"))

    def log_error(self, message):
        print(colored(f"ERROR: {message}", "red"))

    def log_election(self, message):
        print(colored(f"ELECTION: {message}", "blue"))
