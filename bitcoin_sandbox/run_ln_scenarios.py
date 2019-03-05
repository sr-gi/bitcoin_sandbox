from time import sleep
from bitcoin_sandbox.rpc_utils import *
from bitcoin_sandbox.docker_utils import *
from bitcoin_sandbox.ln_rpc_utils import getinfo, newaddr, connect, listpeers, fundchannel, listfunds
from ln_node import LN_Node


def get_address_from_info(info, version='ipv4'):
    ip = None
    port = None
    addresses = info.get('address')

    for address in addresses:
        if address.get('type') == version:
            ip = address.get('address')
            port = address.get('port')

    if addresses is None and port is None:
        message = "No ip:port found for the provided ip version (%s)" % version
        raise Exception(message)

    return ip, port


def create_onchain_setup(client, btc_containers):
    btc_addrs = {}

    for node in btc_containers:
        # Get the ip of each node
        rpc_server = get_ip_by_container_name(client, node.name)

        # Run lightningd in every container
        node.exec_run('lightningd', detach=True)
        logging.info("  running lightningd in node {}".format(node.name))

        # Give time to lightningd to start
        sleep(1)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        btc_addr = newaddr(node)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        logging.info("  generating a new address for node {}: {}".format(node.name, btc_addr))

        block_id = rpc_call(client, rpc_server, call='generatetoaddress', arguments="1 , '%s'" % btc_addr)[0]
        logging.info("  new block mined: {}. Reward sent to {}".format(block_id, btc_addr))

        btc_addrs[node.name] = btc_addr

    # Generate 100 blocks on top of this so all funds are mature (we can give this to the last node, it doesn't matter)
    rpc_call(client, rpc_server, call='generate', arguments='100')
    logging.info("  generating 100 additional blocks so all the previous funds are mature")

    return btc_addrs


def get_ln_nodes_info(btc_containers, btc_addrs):
    ln_node_info = {}

    for node in btc_containers:
        raw_info = getinfo(node)

        ln_node_id = raw_info.get('id')
        ln_node_ip, ln_node_port = get_address_from_info(raw_info)
        ln_node_btc_addr = btc_addrs[node.name]

        ln_node = LN_Node(node_id=ln_node_id, ip=ln_node_ip, port=ln_node_port, btc_addr=ln_node_btc_addr)
        ln_node_info[node.name] = ln_node

    return ln_node_info


def wait_until_mature(btc_containers):
    all_available = False
    notified = False

    while not all_available:
        funds = [listfunds(node).get("outputs") for node in btc_containers]
        all_available = all(out != [] for out in funds)

        if not all_available:
            if not notified:
                logging.info("  waiting for funds to show up in lightningd")
            sleep(5)


def create_ln_scenario_from_graph_file(client, ln_nodes_info, graph_file):
    """
    Creates a network with the topology extracted from a graphml file.

    :param client: docker client
    :param graph_file: .graphml file with the network topology
    :return:
    """
    logging.info("Creating LN scenario from graph file")
    g = nx.read_graphml(graph_file, node_type=int)
    create_ln_scenario_from_graph(client, ln_nodes_info, g)


def create_ln_scenario_from_graph(client, ln_nodes_info, g):

    """
    Creates a LN network with the topology extracted from a graph.

    :param client: docker client
    :param g: networkx graph
    :return:
    """

    # Plot graph
    # nx.draw(g)
    # plt.draw()
    # plt.show(block=True)

    logging.info("  Graph file contains {} nodes and {} connections".format(len(g.nodes()), len(g.edges())))

    for edge in g.edges():
        source = DOCK_CONTAINER_NAME_PREFIX + str(edge[0])
        dst = DOCK_CONTAINER_NAME_PREFIX + str(edge[1])

        source_container = client.containers.get(source)
        dst_info = ln_nodes_info.get(dst)

        # Create connection
        logging.info("  creating LN connection ({}, {})".format(source, dst))
        peer_id = connect(source_container, dst_info.id, dst_info.ip, dst_info.port)
        logging.info("      peer id: {}".format(peer_id))

        # Open channel
        logging.info("  funding channel: {} --> {}".format(source, dst))
        channel_info = fundchannel(source_container, dst_info.id, 10000)
        logging.info("      channel id: {}".format(channel_info.get('channel_id')))

    # TODO: CHECK THIS
    # Generate more blocks so funding transaction is locked
    rpc_server = get_ip_by_container_name(client, source)
    rpc_call(client, rpc_server, call='generate', arguments='15')
    logging.info("  generating 15 additional blocks to lock funding transaction")


def build_simulation_env(client):
    # Get all nodes
    btc_containers = [container for container in client.containers.list("all") if 'btc_n' in container.name]
    btc_containers.reverse()

    # Give every node some bitcoins to start with
    btc_addrs = create_onchain_setup(client, btc_containers)

    # Wait until lightningd has processed all new blocks so funds show up in every node
    wait_until_mature(btc_containers)

    # Run the LN nodes on top of bitcoind
    ln_nodes_info = get_ln_nodes_info(btc_containers, btc_addrs)

    create_ln_scenario_from_graph_file(client, ln_nodes_info, TEST_LN_GRAPH_FILE_1)


if __name__ == '__main__':
    # Create docker client
    client = docker.from_env()

    # Configure logging
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO, handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ])

    build_simulation_env(client)