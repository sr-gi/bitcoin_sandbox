from json import loads


def lightning_rpc(container, command, params=[]):
    command = 'lightning-cli ' + command

    for param in params:
        command += ' ' + str(param)

    rcode, result = container.exec_run(command)

    print container.name, command

    if rcode in [0, None]:
        return loads(result)
    else:
        raise Exception(result, rcode)


def listpeers(container):
    return lightning_rpc(container, 'listpeers').get('peers')


def getinfo(container):
    return lightning_rpc(container, 'getinfo')


def newaddr(container):
    return lightning_rpc(container, 'newaddr').get('address')


def connect(container, peer_id, peer_ip, peer_port):
    return lightning_rpc(container, 'connect', [peer_id, peer_ip, peer_port]).get('id')


def fundchannel(container, peer_id, amount):
    return lightning_rpc(container, 'fundchannel', [peer_id, amount])


def listfunds(container):
    return lightning_rpc(container, 'listfunds')
