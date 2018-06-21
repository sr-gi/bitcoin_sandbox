from bitcoin_sandbox.conf import *
from bitcoin_sandbox.docker_utils import *
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import networkx as nx


def rpc_getinfo(client, rpc_server, rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Tests a rpc connection to a given container.
    :param client: docker client
    :param rpc_server: container IP (with bitcoind running)
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: boolean, whether the connection was successful
    """
    try:
        rpc_server = get_ip_by_unknown(client, rpc_server)
        # Test connection by sending a getinfo command
        rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpc_user, rpc_password, rpc_server, rpc_port))
        get_info = rpc_connection.getinfo()
        return get_info
    except JSONRPCException as err:
        return False


def rpc_test_connection(client, rpc_server, rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Tests a rpc connection to a given container.
    :param client: docker client
    :param rpc_server: container IP (with bitcoind running)
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: boolean, whether the connection was successful
    """
    try:
        get_info = rpc_getinfo(client, rpc_server, rpc_user=rpc_user, rpc_password=rpc_password, rpc_port=rpc_port)
        print get_info
        return True
    except JSONRPCException as err:
        return False


def rpc_getpeerinfo(client, rpc_server, rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Sends a rpc: getpeerinfo call to a given container.
    :param client: docker client
    :param rpc_server: container IP (with bitcoind running)
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: result of the rpc call or False
    """
    try:
        rpc_server = get_ip_by_unknown(client, rpc_server)
        rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpc_user, rpc_password, rpc_server, rpc_port))
        peerinfo = rpc_connection.getpeerinfo()
        return peerinfo
    except JSONRPCException as err:
        return False


def rpcp_get_peer_ips(client, rpc_server, rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Returns a list of ips addresses of the peers connected to the node, together with a boolean indicating
    in the connection is inboud.
    :param client: docker client
    :param rpc_server: container IP (with bitcoind running)
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: list of tuples, each tuple has (IP, inbound?)
    """
    peerinfo = rpc_getpeerinfo(client, rpc_server, rpc_user=rpc_user, rpc_password=rpc_password, rpc_port=rpc_port)
    peer_ips = []

    for peer in peerinfo:
        if ':' in peer['addr']:
            peer_ip, peer_port = str.split(str(peer['addr']), ':')
        else:
            peer_ip = str(peer["addr"])
        
        peer_ips.append((peer_ip, peer["inbound"]))

    return peer_ips


def rpc_create_connection(client, source, dest,
                          rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Creates a connection between two bitcoind nodes (from source to dest).
    Both ends must be running a bitcoind instance.

    :param client: docker client
    :param source: container IP (with bitcoind running)
    :param dest: container IP (with bitcoind running)
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: boolean, whether the connection was successful
    """
    try:
        source = get_ip_by_unknown(client, source)
        dest = get_ip_by_unknown(client, dest)

        rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpc_user, rpc_password, source, rpc_port))
        rpc_connection.addnode(dest, "add")
        return True
    except JSONRPCException as err:
        print err
        return False


def rpc_call(client, rpc_server, call, arguments=None,
                     rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Sends a rpc call to a given container.

    :param client: docker client
    :param rpc_server: container IP (with bitcoind running)
    :param call: rpc call to send
    :param arguments: arguments to the rpc call
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: result of the rpc call or False
    """
    try:
        rpc_server = get_ip_by_unknown(client, rpc_server)
        rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpc_user, rpc_password, rpc_server, rpc_port))
        args = "(" + arguments + ")" if arguments else "()"
        r = eval("rpc_connection." + call + args)
        return r
    except JSONRPCException as err:
        print err
        return False


def rpc_call_to_all(client, call, prefix=DOCK_CONTAINER_NAME_PREFIX, arguments=None,
                    rpc_user=BTC_RPC_USER, rpc_password=BTC_RPC_PASSWD, rpc_port=BTC_RPC_PORT):
    """
    Sends a rpc call to all containers with a given prefix in their name.

    :param client: docker client
    :param call: rpc call to send
    :param prefix: string, prefix to find in containers' names
    :param arguments: arguments to the rpc call
    :param rpc_user: bitcoind rpc user
    :param rpc_password: bitcoind rpc password
    :param rpc_port: bitcoind rpc port
    :return: a list with the results of the rpc calls or False
    """
    try:
        containers = get_containers_names(client, prefix)
        r = []
        for c in containers:
            rpc_server = get_ip_by_unknown(client, c)
            rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpc_user, rpc_password, rpc_server, rpc_port))
            args = "(" + arguments + ")" if arguments else "()"
            r.append(eval("rpc_connection." + call + args))
        return r
    except JSONRPCException as err:
        return False


def rpcp_get_network_topology(client, mode='ip', out_format='graph', exclude=None):
    """
    Gets the network topology as a dict.
    :param client: docker client
    :param mode: Whether identifying the peer by its name or ip.
    :param out_format: Whether the return format is text of a graph
    :param exclude: Whether to exclude any node from the topology.
    :return: Network topology
    """

    # Sanity checks
    assert mode in ['ip', 'IP', 'name', 'id'], 'Supported modes are ip ("ip" or "IP") and container name("name").'
    assert out_format in ['text', 'graph'], 'Supported formats are "text" and "graph"'
    if exclude and not isinstance(exclude, list):
        exclude = [exclude]

    # Initialize the container identifier (name or ip) depending on the mode
    containers = map(str, get_containers_names(client))

    # Remove excluded nodes
    if exclude:
        for node in exclude:
            if node in containers:
                containers.remove(node)

    if mode in ['ip', 'IP']:
        containers = [get_ip_by_container_name(client, container) for container in containers]

    # Initialize the net_topology structure depending on the out_format
    if out_format == 'graph':
        net_topology = nx.Graph()
    else:
        net_topology = {}
        for container in containers:
            net_topology[container] = []

    for container in containers:
        # For each container get the list of peer ips.
        for ip, inbound in rpcp_get_peer_ips(client, container):
            # Identify the peer depending on the mode (ip or name)
            if mode == 'name':
                peer = get_container_name_by_ip(client, ip)
            else:
                peer = ip

            # Add an edge between the container and the peer depending on the out_format.
            if peer not in exclude:
                if out_format == 'graph':
                    net_topology.add_edge(container, peer)

                else:
                    net_topology[container].append((peer, inbound))

    return net_topology
