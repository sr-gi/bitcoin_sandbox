from json import loads


def lightning_rpc(container, command, params=[], verbose=False):
    if not isinstance(params, list):
        params = [params]

    command = 'lncli --no-macaroons ' + command

    for param in params:
        command += ' ' + str(param)

    rcode, result = container.exec_run(command)

    if verbose:
        print "\t\t\t\t%s, %s" % (container.name, command)

    if rcode in [0, None]:
        return loads(result)
    else:
        raise Exception(result, rcode)


def listpeers(container):
    return lightning_rpc(container, 'listpeers').get('peers')


def getinfo(container):
    return lightning_rpc(container, 'getinfo')


def newaddress(container):
    return lightning_rpc(container, 'newaddress', 'p2wkh').get('address')


def connect(container, peer_id, peer_ip, peer_port):
    return lightning_rpc(container, 'connect', '{}@{}:{}'.format(peer_id, peer_ip, peer_port)).get('id')


def openchannel(container, peer_id, amount):
    return lightning_rpc(container, 'openchannel', [peer_id, amount]).get('funding_txid')


def listunspent(container):
    return lightning_rpc(container, 'listunspent')