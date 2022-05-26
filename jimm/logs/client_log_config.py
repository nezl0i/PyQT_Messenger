import logging
import os
from common.variables import LOGGING_LEVEL

CLIENT_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(message)s')
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

# Потоки
STEAM_HANDLER = logging.StreamHandler()
STEAM_HANDLER.setFormatter(CLIENT_FORMATTER)
STEAM_HANDLER.setLevel(logging.ERROR)

FILE_HANDLER = logging.FileHandler(PATH, encoding='utf-8')
FILE_HANDLER.setFormatter(CLIENT_FORMATTER)

# Регистратор
LOGGER = logging.getLogger('client')
LOGGER.addHandler(STEAM_HANDLER)
LOGGER.addHandler(FILE_HANDLER)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.warning('Предупреждение')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')

