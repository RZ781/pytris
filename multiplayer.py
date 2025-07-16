import select, socket, random
from typing import List, Tuple, Optional

PYTRIS_PORT = 51737
PROTOCOL_VERSION = 0
CMD_SEND_GARBAGE = 1
CMD_RECEIVE_GARBAGE = 2
CMD_EXIT = -1

class Connection:
    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket
        self.buf = b""
        self.version_sent = False
    def send(self, command: int, data: bytes) -> None:
        self.socket.sendall(bytes([command, len(data) >> 8, len(data) & 0xFF]) + data)
    def recv(self) -> List[Tuple[int, bytes]]:
        r, _, _ = select.select([self], [], [], 0)
        if not r:
            return []
        data = self.socket.recv(1<<16)
        if not data:
            return [(CMD_EXIT, b"")]
        self.buf += data
        commands = []
        while len(self.buf) >= 3:
            command = self.buf[0]
            length = int.from_bytes(self.buf[1:3])
            if len(self.buf) < 3 + length:
                break
            commands.append((command, self.buf[3:3+length]))
            self.buf = self.buf[3+length:]
        return commands
    def fileno(self) -> int:
        return self.socket.fileno()
    def close(self) -> None:
        self.socket.close()

def server() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", PYTRIS_PORT))
        s.listen()
        connections = []
        while True:
            r, _, _ = select.select([s], [], [], 0)
            if r:
                conn, address = s.accept()
                connections.append(Connection(conn))
            for connection in connections.copy():
                for command, data in connection.recv():
                    if command == CMD_SEND_GARBAGE:
                        if len(connections) < 2:
                            continue
                        target = connection
                        while target is connection:
                            target = random.choice(connections)
                        target.send(CMD_RECEIVE_GARBAGE, data)
                    elif command == CMD_EXIT:
                        connection.close()
                        connections.remove(connection)
                    else:
                        exit(f"Unknown command {command}")

def connect_to_server(address: str) -> Optional[Connection]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((address, PYTRIS_PORT))
    except:
        return None
    return Connection(s)
