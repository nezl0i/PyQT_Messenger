import argparse
import json
import logging
import socket
import sys
import threading
import time

from errors import IncorrectDataRecivedError, ServerError, ReqFieldMissingError
from common.utils import get_message, send_message
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, SENDER, MESSAGE, MESSAGE_TEXT, EXIT, DESTINATION
from log_decorator import log
from metacls import ClientVerifier

CLIENT_LOGGER = logging.getLogger('client')


class ClientSendOptions(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except (Exception,):
            CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    def run(self):
        helper()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                helper()
            elif command == 'exit':
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана [help - поддерживаемые команды].')


class ClientReadOptions(threading.Thread):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                       f'\n{message[MESSAGE_TEXT]}')
                else:
                    CLIENT_LOGGER.error(f'Получено некорректное сообщение от сервера: {message}')
            except IncorrectDataRecivedError:
                CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                break


def helper():
    """Справка по командам"""
    print('Поддерживаемые команды:')
    print('message - сформировать сообщение для отправки')
    print('help - подсказки по командам')
    print('exit - выход')


def check_port(port):
    """Проверка порта сокета для клиента"""
    if port not in range(1024, 65536):
        CLIENT_LOGGER.critical(f'Ошибка запуска с портом {port}. Допустимый диапазон портов от 1024 до 65535.')
        sys.exit(1)
    return port


def process_ans(message):
    CLIENT_LOGGER.debug(f'Обработка сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


def create_presence(account_name='Guest'):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


def create_parser():
    parser = argparse.ArgumentParser(description="JIM Client_server application")
    parser.add_argument('-s', '--ip', nargs='?', default=DEFAULT_IP_ADDRESS, help='Server IP')
    parser.add_argument('-p', '--port',  nargs='?', default=DEFAULT_PORT, type=int, help='Server port')
    parser.add_argument('-n', '--name', default='None', nargs='?')
    return parser



def main():

    args = create_parser().parse_args()
    server_port = check_port(args.port)
    server_address = args.ip
    client_name = args.name
    if not client_name:
        client_name = input('Имя пользователя: ')
    CLIENT_LOGGER.info(f'Клиент {client_name} запущен с параметрами: {server_address}:{server_port} ')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_ans(get_message(transport))
        CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except (ConnectionRefusedError, ConnectionError):
        CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                               f'конечный компьютер отверг запрос на подключение.')
    except (ValueError, json.JSONDecodeError):
        CLIENT_LOGGER.error(f'Ошибка декодирования JSON пакета от {server_address}.')
    else:
        receiver = ClientReadOptions(client_name, transport)
        receiver.daemon = True
        receiver.start()

        sender = ClientSendOptions(client_name, transport)
        sender.daemon = True
        sender.start()
        CLIENT_LOGGER.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
