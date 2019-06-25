import bitcoin_sandbox.rpc_utils as bitcoin_cli
import bitcoin_sandbox.ln_rpc_utils as lncli
import networkx as nx
from time import sleep
from bitcoin_sandbox.docker_utils import *
from ln_node import LN_Node


def get_address_from_info(info, version='ipv4'):
    ip = None
    port = None
    addresses = info.get('address')
    print(addresses)

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
        # Run lnd in every container
        node.exec_run('lnd', detach=True)
        logging.info("  running lnd in node {}".format(node.name))

        # Give time to lnd to start
        sleep(4)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        btc_addr = lncli.newaddress(node)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        logging.info("  generating a new address for node {}: {}".format(node.name, btc_addr))

        block_id = str(bitcoin_cli.generatetoaddress(node, 1, btc_addr)[0])
        logging.info("  new block mined: {}. Reward sent to {}".format(block_id, btc_addr))

        btc_addrs[node.name] = btc_addr

    # Generate 100 blocks on top of this so all funds are mature (we can give this to the last address, does not matter)
    bitcoin_cli.generatetoaddress(btc_containers[0], 100, btc_addr)
    logging.info("  generating 100 additional blocks so all the previous funds are mature")

    return btc_addrs


def get_ln_nodes_info(btc_containers, btc_addrs):
    ln_node_info = {}

    for node in btc_containers:
        raw_info = lncli.getinfo(node)

        ln_node_id = raw_info.get('identity_pubkey')
        ln_node_ip = get_container_ip(node)
        # ToDo: Hardcoded port, maybe param in a future?
        ln_node_port = '9735'
        ln_node_btc_addr = btc_addrs[node.name]

        ln_node = LN_Node(node_id=ln_node_id, ip=ln_node_ip, port=ln_node_port, btc_addr=ln_node_btc_addr)
        ln_node_info[node.name] = ln_node

    return ln_node_info


def wait_until_mature(btc_containers):
    all_available = False
    notified = False

    while not all_available:
        funds = [lncli.listunspent(node).get("outputs") for node in btc_containers]
        all_available = all(out != [] for out in funds)

        if not all_available:
            if not notified:
                logging.info("  waiting for funds to show up in lnd")
                notified = True
            sleep(5)


def create_ln_scenario_from_graph(btc_containers, btc_addrs, g):
    # ToDo: Check what was the purpose of this function! Can we work around it?
    ln_nodes_info = get_ln_nodes_info(btc_containers.values(), btc_addrs)

    logging.info("  Graph file contains {} nodes and {} connections".format(len(g.nodes()), len(g.edges())))
    funding_txids = set()

    for edge in g.edges(data=True):
        source, dst, meta = edge
        source = DOCK_CONTAINER_NAME_PREFIX + str(source)
        dst = DOCK_CONTAINER_NAME_PREFIX + str(dst)

        weight = int(meta.get("weight"))
        weight = DEFAULT_LN_GRAPH_WEIGHT if weight is None else weight

        source_container = btc_containers.get(source)
        dst_info = ln_nodes_info.get(dst)

        # Create connection
        logging.info("  creating LN connection ({}, {})".format(source, dst))
        lncli.connect(source_container, dst_info.id, dst_info.ip, dst_info.port)
        logging.info("      peer id: {}".format(dst_info.id))

        # Open channel
        logging.info("  funding channel: {} --> {}".format(source, dst))
        funding_txid = lncli.openchannel(source_container, dst_info.id, weight)
        funding_txids.add(funding_txid)

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
    bitcoin_cli.generatetoaddress(btc_containers.values()[0], 6, btc_addrs.values()[0])
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

    # Wait until lnd has processed all new blocks so funds show up in every node
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
