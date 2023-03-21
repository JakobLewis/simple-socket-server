import socket, threading
from typing import Callable, Tuple, Any
from time import sleep

Request_Handler_Func = Callable[[socket.socket, str, int], None]

class Server(object):

    ip: str
    port: int
    request_handler: Request_Handler_Func
    request_socket: socket.socket

    thread = None

    @staticmethod
    def quickstart(port: int, handler: Request_Handler_Func):
        return Server(socket.gethostbyname(socket.gethostname()), port, handler)

    def __init__(self, ip: str, port: int, handler: Request_Handler_Func):
        self.ip = ip
        self.port = port
        self.request_handler = handler
        self.request_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.request_socket.bind((self.ip, self.port))

    @staticmethod
    def acceptor(func: Request_Handler_Func, sock: socket.socket, can_accept: Callable[[], bool]):
        while True:
            connection, (ip, port) = sock.accept()
            if not can_accept(): return
            func(connection, ip, port)

    def serve_forever(self):
        self.request_socket.listen(5)
        self.acceptor(
            self.request_handler,
            self.request_socket,
            lambda: True
        )

    def start(self):
        self.request_socket.listen(5)
        self.accepting = True

        self.thread = threading.Thread(
            target = Server.acceptor,
            args=(
                self.request_handler,
                self.request_socket,
                lambda: self.thread is not None
            ),
            daemon=True,
        )

        self.thread.start()
    
    def stop(self):
        if self.thread is None: return

        temp_thread = self.thread
        self.thread = None

        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.ip, self.port))
        except:
            pass
        
        temp_thread.join(5)

    @property
    def is_accepting(self) -> bool:
        return self.thread is not None
