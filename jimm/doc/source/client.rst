Client module documentation
=================================================

Клиентское приложение для обмена сообщениями. Поддерживает
отправку сообщений пользователям которые находятся в сети, сообщения шифруются
с помощью алгоритма RSA с длинной ключа 2048 bit.

Поддерживает аргументы командной строки:

``python client.py {имя сервера} {порт} -n или --name {имя пользователя} -p или -password {пароль}``

1. {имя сервера} - адрес сервера сообщений.
2. {порт} - порт по которому принимаются подключения
3. -n или --name - имя пользователя с которым произойдёт вход в систему.
4. -p или --password - пароль пользователя.

Все опции командной строки являются необязательными, но имя пользователя и пароль необходимо использовать в паре.

Примеры использования:

* ``python client.py``

*Запуск приложения с параметрами по умолчанию.*

* ``python client.py ip_address some_port``

*Запуск приложения с указанием подключаться к серверу по адресу ip_address:port*

* ``python -n test1 -p 123``

*Запуск приложения с пользователем test1 и паролем 123*

* ``python client.py ip_address some_port -n test1 -p 123``

*Запуск приложения с пользователем test1 и паролем 123 и указанием подключаться к серверу по адресу ip_address:port*

client.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

client. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:
    
    * адрес сервера
    * порт
    * имя пользователя
    * пароль

    Выполняет проверку на корректность номера порта.


client_db.py
~~~~~~~~~~~~~~

.. autoclass:: client_app.client_db.ClientDatabase
    :members:
    :noindex:

transport.py
~~~~~~~~~~~~~~

.. autoclass:: client_app.transport.ClientTransport
    :members:
    :noindex:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: client_app.main_window.ClientMainWindow
    :members:
    :noindex:

start_dialog.py
~~~~~~~~~~~~~~~

.. autoclass:: client_app.start_dialog.UserNameDialog
    :members:
    :noindex:

add_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client_app.add_contact.AddContactDialog
    :members:
    :noindex:

del_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client_app.del_contact.DelContactDialog
    :members:
    :noindex:
