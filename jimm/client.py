import argparse
import json
import logging
import socket
import sys
import threading
import time

from errors import IncorrectDataRecivedError, ServerError, ReqFieldMissingError
from common.utils import get_message, send_message
from common.variables import *
from log_decorator import log
from metacls import ClientVerifier
from common.helper import client_help
from client_db import ClientDatabase


CLIENT_LOGGER = logging.getLogger('client')
sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
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
        with database_lock:
            if not self.database.check_user(to_user):
                CLIENT_LOGGER.error(f'Попытка отправить сообщение '
                                    f'незарегистрированному получателю: {to_user}')
                return
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        with database_lock:
            self.database.save_message(self.account_name, to_user, message)
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
            except (Exception,):
                CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                sys.exit(1)

    def run(self):
        client_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                client_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                        pass
                    print('Завершение соединения.')
                    CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('Команда не распознана [help - поддерживаемые команды].')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемого контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    CLIENT_LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        CLIENT_LOGGER.error('Не удалось отправить информацию на сервер.')


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError):
                    CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE \
                            and SENDER in message \
                            and DESTINATION in message \
                            and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.account_name:
                        print(f'\n Получено сообщение от пользователя '
                              f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                CLIENT_LOGGER.error('Ошибка взаимодействия с базой данных')

                        CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                                           f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')


def check_port(port):
    if port not in range(1024, 65536):
        CLIENT_LOGGER.critical(f'Ошибка запуска с портом {port}. Допустимый диапазон портов от 1024 до 65535.')
        sys.exit(1)
    return port


@log
def process_ans(message):
    CLIENT_LOGGER.debug(f'Обработка сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
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


@log
def create_parser():
    parser = argparse.ArgumentParser(description="JIM Client_server application")
    parser.add_argument('-s', '--ip', nargs='?', default=DEFAULT_IP_ADDRESS, help='Server IP')
    parser.add_argument('-p', '--port',  nargs='?', default=DEFAULT_PORT, type=int, help='Server port')
    parser.add_argument('-n', '--name', default='None', nargs='?')
    return parser


def contacts_list_request(sock, name):
    CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    CLIENT_LOGGER.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


def user_list_request(sock, username):
    CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    CLIENT_LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


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
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        CLIENT_LOGGER.debug('Запущены процессы')

        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
