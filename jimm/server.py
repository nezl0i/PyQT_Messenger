import select
import argparse
import socket
import logging
import threading

import logs.server_log_config
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, SENDER, MESSAGE, MESSAGE_TEXT, EXIT, RESPONSE_200, RESPONSE_400, \
    DESTINATION
from common.utils import get_message, send_message
from descriptors import Port
from metacls import ServerVerifier
from server_db import ServerDatabase
from common.helper import server_help


SERVER_LOGGER = logging.getLogger('server')


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, address, port, database):
        self.addr = address
        self.port = port
        self.sock = None
        self.clients = []
        self.messages = []
        self.names = dict()
        self.database = database
        super().__init__()

    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.addr, self.port))
        self.sock.settimeout(0.8)
        self.sock.listen(MAX_CONNECTIONS)
        SERVER_LOGGER.info(f'Сервер запущен с параметрами: {self.addr}:{self.port}')

    def run(self):
        self.create_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соединение с  {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (Exception,):
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except Exception as e:
                    SERVER_LOGGER.info(f'Связь с клиентом {message[DESTINATION]} была потеряна, ошибка {e}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and \
                self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от {message[SENDER]}.')
        elif message[DESTINATION] in self.names \
                and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован, отправка сообщения невозможна.')

    def process_client_message(self, message, client):
        SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
        if ACTION in message and message[ACTION] == PRESENCE \
                and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                RESPONSE_400[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, RESPONSE_400)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            return
        else:
            RESPONSE_400[ERROR] = 'Запрос некорректен.'
            send_message(client, RESPONSE_400)
            return


def main():
    database = ServerDatabase()
    parser = argparse.ArgumentParser(description="JIM Client_server application")
    parser.add_argument('-a', dest='address', nargs='?', default='127.0.0.1', help='IP address')
    parser.add_argument('-p', dest='port', nargs='?', default=DEFAULT_PORT, type=int, help='Server port')
    args = parser.parse_args()

    server = Server(args.address, args.port, database)
    server.daemon = True
    server.start()

    while True:
        command = input()
        if command == 'help':
            server_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'history':
            name = input('Введите имя пользователя для просмотра истории. '
                         'Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    main()
