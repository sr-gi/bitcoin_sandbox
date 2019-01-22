from json import loads


def lightning_rpc(container, command, params=[]):
    command = 'lightning-cli ' + command

    for param in params:
        command += ' ' + str(param)

    rcode, result = container.exec_run(command)

    if rcode in [0, None]:
        return loads(result)
    else:
        raise Exception(result)


def listpeers(container):
    return lightning_rpc(container, 'listpeers').get('peers')


def getinfo(container):
    return lightning_rpc(container, 'getinfo')


def newaddr(container):
    return lightning_rpc(container, 'newaddr').get('address')

