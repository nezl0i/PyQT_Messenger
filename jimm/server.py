import select
import sys
import argparse
import socket
import json
import logging
import time

import logs.server_log_config
from log_decorator import log
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, SENDER, MESSAGE, MESSAGE_TEXT, EXIT, RESPONSE_200, RESPONSE_400, \
    DESTINATION
from common.utils import get_message, send_message

SERVER_LOGGER = logging.getLogger('server')


@log
def process_client_message(message, messages_list, client, clients, names):
    SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
    if ACTION in message and message[ACTION] == PRESENCE and \
            TIME in message and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    elif ACTION in message and message[ACTION] == MESSAGE and \
            DESTINATION in message and TIME in message \
            and SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    else:
        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен.'
        send_message(client, response)
        return


@log
def process_message(message, names, listen_socks):
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        SERVER_LOGGER.info(f'Сообщение отправлено пользователю {message[DESTINATION]} '
                           f'от {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(
            f'Не удалось отправить сообщение, пользователь {message[DESTINATION]} не зарегистрирован.')


@log
def check_port(port):
    if port not in range(1024, 65536):
        SERVER_LOGGER.critical(f'Ошибка запуска сервера с портом {port}. Допустимый диапазон портов от 1024 до 65535.')
        sys.exit(1)
    return port


def main():
    parser = argparse.ArgumentParser(description="JIM Client_server application")

    parser.add_argument('-a', dest='address', nargs='?', default='127.0.0.1', help='IP address')
    parser.add_argument('-p', dest='port', nargs='?', default=DEFAULT_PORT, type=int, help='Server port')
    args = parser.parse_args()

    listen_port = check_port(args.port)
    listen_address = args.address

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.8)
    transport.listen(MAX_CONNECTIONS)
    SERVER_LOGGER.info(f'Сервер запущен с параметрами: {listen_address}:{listen_port}')

    # Список клиентов
    clients = []
    # Очередь сообщений
    messages = []
    # Словарь, содержащий имена пользователей и сокеты.
    names = dict()  # {client_name: client_socket}

    while True:
        try:
            client, client_address = transport.accept()
            SERVER_LOGGER.info(f'Установлено соединение с {client_address}')
            clients.append(client)
        except OSError as err:
            print(err.errno)

        recv_data_lst = []
        send_data_lst = []
        err_lst = []

        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message, clients, names)
                except Exception:
                    SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                       f'отключился от сервера.')
                    clients.remove(client_with_message)

        # Если есть сообщения, обрабатываем каждое.
        for i in messages:
            try:
                process_message(i, names, send_data_lst)
            except Exception:
                SERVER_LOGGER.info(f'Связь с клиентом {i[DESTINATION]} была потеряна')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()


if __name__ == '__main__':
    main()
