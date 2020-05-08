import asyncio
from asyncio import transports
from typing import Optional


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None



    def data_received(self, data: bytes):
        decoded = data.decode()

        print(decoded)

        if self.login is None:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if len(["" for client in self.server.clients
                        if str(client.login).lower() == str(login).lower()
                           and client != self
                        ]
                       ) > 0:
                    self.transport.write(
                        f"Login {login} is already in use, try another one ".encode()
                    )
                    self.connection_lost(ConnectionRefusedError)
                else:
                    self.login = login
                    self.transport.write(
                        f"Hi {self.login}!".encode()
                    )
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        self.server.last_messages.append(format_string)
        if len(self.server.last_messages)>10:
            self.server.last_messages.pop(0)
        encoded = format_string.encode()
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Connecton established")


    def connection_lost(self, exc: Optional[Exception]):
        self.server.clients.remove(self)
        print("Connection lost")

    def send_history(self):
        for message in self.server.last_messages:
            self.transport.write(
                f"{message}\n".encode()
            )

class Server:
    clients: list
    last_messages: list
    def __init__(self):
        self.clients = []
        self.last_messages = []
    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Server started ...")
        await coroutine.serve_forever()

process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server stopped by user")
