import asyncio
from asyncio import transports

class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'): # одинарные кавычки для более позднего объявления класса
        self.server = server

    def send_history(self):
        for message in self.server.history[-10:]:
            self.transport.write(message.encode())

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is not None:
            self.send_message(decoded)
            self.server.history.append(f"{self.login}: {decoded}")
        else:
            if decoded.startswith("login: "):
                temp_login = decoded.replace("login:", "").replace("\r\n", "").strip()
                is_login_unique = True
                for login_list in self.server.clients:
                    if login_list.login == temp_login: is_login_unique = False

                if is_login_unique == True:
                    self.login = temp_login
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.send_history()
                else:
                    self.transport.write(f"Логин {temp_login} занят, попробуйте другой.\n".encode())
                    self.transport.close()
            else:
                self.transport.write("Неправильный логин. Для входа наберите ""login: логин""\n".encode())


    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for users in self.server.clients:
            users.transport.write(message.encode())

class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()

process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")