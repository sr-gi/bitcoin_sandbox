import bitcoin_sandbox.rpc_utils as bitcoin_cli
import bitcoin_sandbox.ln_rpc_utils as lightning_cli
import networkx as nx
from time import sleep
from bitcoin_sandbox.docker_utils import *
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


def create_onchain_setup(btc_containers):
    btc_addrs = {}

    for node in btc_containers:
        # Run lightningd in every container
        node.exec_run('lightningd', detach=True)
        logging.info("  running lightningd in node {}".format(node.name))

        # Give time to lightningd to start
        sleep(2)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        btc_addr = lightning_cli.newaddr(node)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        logging.info("  generating a new address for node {}: {}".format(node.name, btc_addr))

        block_id = str(bitcoin_cli.generatetoaddress(node, 1, btc_addr)[0])
        logging.info("  new block mined: {}. Reward sent to {}".format(block_id, btc_addr))

        btc_addrs[node.name] = btc_addr

    # Generate 100 blocks on top of this so all funds are mature (we can give this to the first node, it doesn't matter)
    bitcoin_cli.generate(btc_containers[0], 100)
    logging.info("  generating 100 additional blocks so all the previous funds are mature")

    return btc_addrs


def get_ln_nodes_info(btc_containers, btc_addrs):
    ln_node_info = {}

    for node in btc_containers:
        raw_info = lightning_cli.getinfo(node)

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
        funds = [lightning_cli.listfunds(node).get("outputs") for node in btc_containers]
        all_available = all(out != [] for out in funds)

        if not all_available:
            if not notified:
                logging.info("  waiting for funds to show up in lightningd")
                notified = True
            sleep(5)


def create_ln_scenario_from_graph(btc_containers, btc_addrs, g):
    # ToDo: Check what was the purpose of this function! Can we work around it?
    ln_nodes_info = get_ln_nodes_info(btc_containers.values(), btc_addrs)

    logging.info("  Graph file contains {} nodes and {} connections".format(len(g.nodes()), len(g.edges())))
    funding_txids = set()

    for edge in g.edges():
        source = DOCK_CONTAINER_NAME_PREFIX + str(edge[0])
        dst = DOCK_CONTAINER_NAME_PREFIX + str(edge[1])

        source_container = btc_containers.get(source)
        dst_info = ln_nodes_info.get(dst)

        # Create connection
        logging.info("  creating LN connection ({}, {})".format(source, dst))
        peer_id = lightning_cli.connect(source_container, dst_info.id, dst_info.ip, dst_info.port)
        logging.info("      peer id: {}".format(peer_id))

        # Open channel
        logging.info("  funding channel: {} --> {}".format(source, dst))
        channel_info = lightning_cli.fundchannel(source_container, dst_info.id, 10000)
        logging.info("      channel id: {}".format(channel_info.get('channel_id')))
        funding_txids.add(channel_info.get('txid'))

    # Give some time to the funding transactions to propagate
    logging.info("  waiting until funding transactions have been spread")
    spread = False
    while not spread:
        mempools = [bitcoin_cli.getrawmempool(container) for container in btc_containers.values()]
        spread = (set(mempool) == funding_txids for mempool in mempools)
        spread = all(spread)
        if not spread:
            sleep(2)

    # Generate more blocks so funding transaction is locked (to node 0)
    bitcoin_cli.generate(btc_containers.values()[0], 6)
    logging.info("  generating 6 additional blocks to lock funding transaction")


def create_ln_scenario_from_graph_file(btc_containers, btc_addrs, graph_file):
    logging.info("  Creating LN scenario from graph file")
    g = nx.read_graphml(graph_file, node_type=int)
    create_ln_scenario_from_graph(btc_containers, btc_addrs, g)


def build_simulation_env(client):
    # Get all nodes
    btc_containers = {container.name: container for container in client.containers.list("all") if 'btc_n' in
                      container.name}

    # Give every node some bitcoins to start with
    btc_addrs = create_onchain_setup(btc_containers.values())

    # Wait until lightningd has processed all new blocks so funds show up in every node
    wait_until_mature(btc_containers.values())

    # Run the LN nodes on top of bitcoind
    create_ln_scenario_from_graph_file(btc_containers, btc_addrs, LN_GRAPH_FILE)


if __name__ == '__main__':
    # Create docker client
    client = docker.from_env()

    # Configure logging
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO, handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ])

    build_simulation_env(client)
