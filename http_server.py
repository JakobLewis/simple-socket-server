from server import Server, socket
from os.path import normpath, exists
from os import mkdir
from time import gmtime, strftime, struct_time
from typing import Optional

BAD_REQUEST = 'HTTP/1.1 400 Bad Request\r\n\r\n'.encode()
NOT_FOUND = 'HTTP/1.1 404 Not Found\r\n\r\n'.encode()
BAD_METHOD = 'HTTP/1.1 405 Method Not Allowed\r\n\r\n'.encode()
CLIENT_TIMEOUT = 'HTTP/1.1 408 Request Timeout\r\n\r\n'.encode()
INTERNAL_ERROR = 'HTTP/1.1 500 Internal Server Error\r\n\r\n'.encode()

ASSET_PATH = '\\'.join(__file__.split('\\')[:-1]) + '\\assets'
INDEX_PATH = normpath(ASSET_PATH + '/Doug\'s World.htm')

def http_timestamp(t: struct_time) -> str:
    return strftime("%a, %d %b %Y %H:%M:%S GMT", t)

def ok_response(content: bytes, last_modified: Optional[struct_time] = None) -> bytes:
    r_str = 'HTTP/1.1 200 OK\r\n'.encode()
    r_str += f'Date: {http_timestamp(gmtime())}\r\n'.encode()
    if last_modified != None: r_str += f'Last-Modified: {http_timestamp(last_modified)}\r\n'.encode()
    r_str += 'Accept-Ranges: bytes\r\n'.encode()
    r_str += f'Content-Length: {len(content)}\r\n'.encode()
    r_str += 'Content-Type: text/html; charset-UTF-8\r\n\r\n'.encode()
    r_str += content

    return r_str

class Http_Server(Server):
    internal_server: Server

    def __init__(self, port: int):
        if not exists(ASSET_PATH): mkdir(ASSET_PATH)
        super().__init__(socket.gethostbyname(socket.gethostname()), port, self.parse)

    @staticmethod
    def parse(sock: socket.socket, ip: str, port: int):

        sock.settimeout(5)
        http_str = ''
        method = ''
        path = ''

        try:
            binary_packet = b''
            while binary_packet[-4:] != b'\r\n\r\n':
                binary_packet += sock.recv(1);

            http_str = binary_packet.decode()
            first_line_args = http_str[0:http_str.index('\r\n')].split(' ')

            method, path, *_ = first_line_args
        except socket.timeout as e:
            print(f'[{ip}:{port}]: Timeout "{e}"')
            sock.sendall(CLIENT_TIMEOUT)
            sock.close()
            return
        except Exception as e:
            print(f'[{ip}:{port}]: Error "{e}" with header "{http_str}"')
            sock.sendall(BAD_REQUEST)
            sock.close()
            return
        
        if method != 'GET':
            print(f'[{ip}:{port}]: Method "{method}" not supported with header "{path}"')
            sock.sendall(BAD_METHOD)
            sock.close()
            return
        
        print(f'[{ip}:{port}]: Acessing "{path}"... ', end='')
        
        try:
            normed_path = normpath(ASSET_PATH + path).replace('%20', ' ')
            if not normed_path.startswith(ASSET_PATH): raise FileNotFoundError('Possible path traversal: ' + normed_path)
            if normed_path == ASSET_PATH: normed_path = INDEX_PATH

            file_handle = open(normed_path, 'rb')
            content = file_handle.read()
            file_handle.close()

            sock.sendall(ok_response(content))
            sock.close()
            print('Success')

        except FileNotFoundError as e:
            print(f'FileNotFound "{e}"')
            sock.sendall(NOT_FOUND)
            sock.close()
            return
        except Exception as e:
            print(f'Error "{e}" with header "{http_str}"')
            sock.sendall(INTERNAL_ERROR)
            sock.close()
            return
        
if __name__ == '__main__':
    server = Http_Server(12001)
    print(f'Serving on {server.ip}:{server.port}')
    server.serve_forever()