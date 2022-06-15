import dis


class ClientVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        LOAD_GLOBAL = set()
        for func in cls_dict:
            try:
                opcode = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for _ in opcode:
                    if _.opname == 'LOAD_GLOBAL':
                        LOAD_GLOBAL.add(_.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in LOAD_GLOBAL:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        if 'get_message' in LOAD_GLOBAL or 'send_message' in LOAD_GLOBAL:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(cls_name, bases, cls_dict)


class ServerVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        LOAD_GLOBAL = set()
        LOAD_METHOD = set()
        LOAD_ATTR = set()
        for func in cls_dict:
            try:
                opcode = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for _ in opcode:
                    if _.opname == 'LOAD_GLOBAL':
                        LOAD_GLOBAL.add(_.argval)
                    elif _.opname == 'LOAD_METHOD':
                        LOAD_METHOD.add(_.argval)
                    elif _.opname == 'LOAD_ATTR':
                        LOAD_ATTR.add(_.argval)
        # print(20*'-', 'methods', 20*'-')
        # print(LOAD_GLOBAL)
        # print(20*'-', 'methods_2', 20*'-')
        # print(LOAD_METHOD)
        # print(20*'-', 'attrs', 20*'-')
        # print(LOAD_ATTR)

        if 'connect' in LOAD_GLOBAL:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in LOAD_ATTR and 'AF_INET' in LOAD_ATTR):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(cls_name, bases, cls_dict)
