from json import loads


def lightning_rpc(container, command, params=[], verbose=False):
    if not isinstance(params, list):
        params = [params]

    command = 'lncli --no-macaroons ' + command

    for param in params:
        command += ' ' + str(param)

    if verbose:
        print "\t\t\t\t%s, %s" % (container.name, command)

    rcode, result = container.exec_run(command)

    if rcode in [0, None]:
        return loads(result)
    else:
        raise Exception(result, rcode)


def listpeers(container, verbose=False):
    return lightning_rpc(container, 'listpeers', verbose=verbose).get('peers')


def getinfo(container, verbose=False):
    return lightning_rpc(container, 'getinfo', verbose=verbose)


def newaddress(container, addr_type='p2wkh', verbose=False):
    assert addr_type in ['p2wkh', 'np2wkh'], "Wrong address type. Try 'p2wkh' or 'np2wkh'"
    return lightning_rpc(container, 'newaddress', 'p2wkh', verbose=verbose).get('address')


def connect(container, peer_id, peer_ip, peer_port, verbose=False):
    return lightning_rpc(container, 'connect', '{}@{}:{}'.format(peer_id, peer_ip, peer_port),
                         verbose=verbose).get('id')


def openchannel(container, peer_id, amount, verbose=False):
    return lightning_rpc(container, 'openchannel', [peer_id, amount], verbose=verbose).get('funding_txid')


def listunspent(container, verbose=False):
    return lightning_rpc(container, 'listunspent', verbose=verbose)


def describegraph(container, verbose=False):
    return lightning_rpc(container, "describegraph", verbose=verbose)


def sendtoroute(container, payment_hash, route, verbose=False):
    return lightning_rpc(container, "sendtoroute", ["--pay_hash={}".format(payment_hash), "-r='{}'".format(route)],
                         verbose=verbose)


def getheight(container, verbose=False):
    return getinfo(container, verbose=verbose).get('block_height')


def getidentity(container, verbose=False):
    return getinfo(container, verbose=verbose).get('identity_pubkey')