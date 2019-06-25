import bitcoin_sandbox.rpc_utils as bitcoin_cli
import networkx as nx
from docker_utils import get_container_ip


def get_peer_ips(container):
    """
    Returns a list of ips addresses of the peers connected to the node, together with a boolean indicating
    in the connection is inboud.
    :param container: target node to get peers from
    :return: list of tuples, each tuple has (IP, inbound?)
    """

    peerinfo = bitcoin_cli.getpeerinfo(container)
    peer_ips = []

    for peer in peerinfo:
        if ':' in peer['addr']:
            peer_ip, peer_port = str.split(str(peer['addr']), ':')
        else:
            peer_ip = str(peer["addr"])

        peer_ips.append((peer_ip, peer["inbound"]))

    return peer_ips


def get_network_topology(containers, mode='ip', out_format='graph'):
    """
    Gets the network topology as a dict.
    :param containers: The list of containers that form the network
    :param mode: Whether identifying the peer by its name or ip.
    :param out_format: Whether the return format is text of a graph
    :return: Network topology
    """

    # Sanity checks
    assert out_format in ['text', 'graph'], 'Supported formats are "text" and "graph"'

    for container in containers:
        get_container_ip(container)

    if mode in ['name', 'id']:
        # ToDo: Check this for efficiency
        name_ip_map = {get_container_ip(container): container.name for container in containers}
        containers = {str(container.name): container for container in containers}

    elif mode in ['ip', 'IP']:
        containers = {get_container_ip(container): container for container in containers}

    else:
        raise Exception('Supported modes are ip ("ip" or "IP") and container name("name").')

    # Initialize the net_topology structure depending on the out_format
    if out_format == 'graph':
        net_topology = nx.Graph()
    else:
        net_topology = {}
        for container in containers.keys():
            net_topology[container] = []

    for container_id, container in containers.iteritems():
        # For each container get the list of peer ips.
        for ip, inbound in get_peer_ips(container):
            # Identify the peer depending on the mode (ip or name)
            if mode == 'name':
                # ToDo: Check this for efficiency
                # peer = get_container_name_by_ip(client, ip)
                peer = name_ip_map.get(ip)
            else:
                peer = ip

            # Add an edge between the container and the peer depending on the out_format.
            if out_format == 'graph':
                net_topology.add_edge(container_id, peer)

            else:
                net_topology[container_id].append((peer, inbound))

    return net_topology


