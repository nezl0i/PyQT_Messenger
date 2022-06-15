import argparse
import os
import sys

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox
from client_app.client_db import ClientDatabase
from client_app.main_window import ClientMainWindow
from client_app.start_dialog import UserNameDialog
from client_app.transport import ClientTransport
from common.variables import *
from common.errors import ServerError
from common.log_decorator import log

CLIENT_LOGGER = logging.getLogger('client')
if sys.platform == 'linux':
    os.environ['XDG_SESSION_TYPE'] = 'x11'


def check_port(port):
    if port not in range(1024, 65536):
        CLIENT_LOGGER.critical(f'Ошибка запуска с портом {port}. Допустимый диапазон портов от 1024 до 65535.')
        sys.exit(1)
    return port


@log
def create_parser():
    parser = argparse.ArgumentParser(description="JIM Client_server application")
    parser.add_argument('ip', nargs='?', default=DEFAULT_IP_ADDRESS, help='Server IP')
    parser.add_argument('port',  nargs='?', default=DEFAULT_PORT, type=int, help='Server port')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    return parser


if __name__ == '__main__':
    args = create_parser().parse_args()
    server_port = check_port(args.port)
    server_address = args.ip
    client_name = args.name
    client_passwd = args.password

    client_app = QApplication(sys.argv)
    transport = None

    start_dialog = UserNameDialog()

    if not client_name or not client_passwd:
        client_app.exec_()

        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            CLIENT_LOGGER.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)
    CLIENT_LOGGER.info(f'Клиент {client_name} запущен с параметрами: {server_address}:{server_port} ')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    CLIENT_LOGGER.debug("Keys successfully loaded.")

    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(server_port, server_address, database, client_name, client_passwd, keys)
        CLIENT_LOGGER.debug("Transport ready.")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)

    transport.daemon = True
    transport.start()

    del start_dialog

    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Chat application - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
