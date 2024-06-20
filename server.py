import threading
import socket


class Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        super(Server, self).__init__()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostname()
        server_config = (host, port)
        self.server_socket.bind(server_config)
        self.server_socket.listen()
        print('Server listening on {}:{}'.format(host, port))

    # ________chatting function _______________

    def accept(self):
        while True:
            client_sock, client_address = self.server_socket.accept()
            print('Accepted connection from {}:{}'.format(
                client_address[0], client_address[1]))
            threading.Thread(target=self._msgHandler,
                             args=(client_sock, client_address), daemon=True).start()

    def _msgHandler(self, clientsocket, addr):
        while True:
            msg = clientsocket.recv(1024)
            # do some checks and if msg == someWeirdSignal: break:
            print(addr, ' >> ', msg)
            # Maybe some code to compute the last digit of PI, play game or anything else can go here and when you are done.
            clientsocket.send(msg)
        clientsocket.close()


if __name__ == "__main__":
    Server_m = Server(3000)
    Server_m.accept()
    Server_m.server_socket.close()
