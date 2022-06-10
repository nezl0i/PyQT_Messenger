import argparse
import sys

from PyQt5.QtWidgets import QApplication

from client_app.client_db import ClientDatabase
from client_app.main_window import ClientMainWindow
from client_app.start_dialog import UserNameDialog
from client_app.transport import ClientTransport
from common.variables import *
from errors import ServerError
from log_decorator import log

CLIENT_LOGGER = logging.getLogger('client')


def check_port(port):
    if port not in range(1024, 65536):
        CLIENT_LOGGER.critical(f'Ошибка запуска с портом {port}. Допустимый диапазон портов от 1024 до 65535.')
        sys.exit(1)
    return port


@log
def create_parser():
    parser = argparse.ArgumentParser(description="JIM Client_server application")
    parser.add_argument('-s', '--ip', nargs='?', default=DEFAULT_IP_ADDRESS, help='Server IP')
    parser.add_argument('-p', '--port',  nargs='?', default=DEFAULT_PORT, type=int, help='Server port')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    return parser


if __name__ == '__main__':
    args = create_parser().parse_args()
    server_port = check_port(args.port)
    server_address = args.ip
    client_name = args.name

    client_app = QApplication(sys.argv)
    transport = None

    if not client_name:
        print(client_name)
        start_dialog = UserNameDialog()
        client_app.exec_()

        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)
    CLIENT_LOGGER.info(f'Клиент {client_name} запущен с параметрами: {server_address}:{server_port} ')
    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.daemon = True

    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Chat application - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
