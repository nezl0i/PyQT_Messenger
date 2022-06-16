Server module
=================================================

Серверный модуль мессенджера. Обрабатывает словари - сообщения, хранит публичные ключи клиентов.

Использование

Модуль поддерживает аргументы командной строки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.
3. --no_gui Запуск только основных функций, без графической оболочки.

* В данном режиме поддерживается только 1 команда: exit - завершение работы.

Примеры использования:

``python server.py -p 8080``

*Запуск сервера на порту 8080*

``python server.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*

``python server.py --no-gui``

*Запуск без графической оболочки*

server.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

server. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:

    * адрес с которого принимать соединения
    * порт
    * флаг запуска GUI

server. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

core.py
~~~~~~~~~~~

.. autoclass:: server_app.core.MessageProcessor
    :members:
    :noindex:

server_db.py
~~~~~~~~~~~~

.. autoclass:: server_app.server_db.ServerDatabase
    :members:
    :noindex:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: server_app.main_window.MainWindow
    :members:
    :noindex:

add_user.py
~~~~~~~~~~~

.. autoclass:: server_app.add_user.RegisterUser
    :members:
    :noindex:

remove_user.py
~~~~~~~~~~~~~~

.. autoclass:: server_app.remove_user.DelUserDialog
    :members:
    :noindex:

config_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server_app.config_window.ConfigWindow
    :members:
    :noindex:

stat_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server_app.stat_window.StatWindow
    :members:
    :noindex:
