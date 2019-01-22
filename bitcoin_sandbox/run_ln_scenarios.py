from bitcoin_sandbox.rpc_utils import *
from bitcoin_sandbox.docker_utils import *
from bitcoin_sandbox.ln_rpc_utils import getinfo, newaddr
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
    for node in btc_containers:
        # Get the ip of each node
        rpc_server = get_ip_by_container_name(client, node.name)

        # Generate some bitcoins for every peer so they have balance to fund LN channels
        btc_addr = rpc_call(client, rpc_server, 'getnewaddress')
        logging.info("  generating a new address for node {}: {}".format(node.name, btc_addr))

        block_id = rpc_call(client, rpc_server, call='generatetoaddress', arguments="1 , '%s'" % btc_addr)[0]
        logging.info("  new block mined: {}. Reward sent to {}".format(block_id, btc_addr))

    # Generate 100 blocks on top of this so all funds are mature (we can give this to the last node, it doesn't matter)
    rpc_call(client, rpc_server, call='generate', arguments='100')
    logging.info("  generating 100 additional blocks so all the previous funds are mature.")


def deploy_ln_nodes(btc_containers):
    ln_nodes = {}

    for node in btc_containers:
        # Run lightningd in every container
        node.exec_run('lightningd', detach=True)
        logging.info("  running lightningd in node {}".format(node.name))

        ln_node_info = getinfo(node)

        ln_node_id = ln_node_info.get('id')
        ln_node_ip, ln_node_port = get_address_from_info(ln_node_info)
        ln_node_btc_addr = newaddr(node)

        ln_node = LN_Node(node_id=ln_node_id, ip=ln_node_ip, port=ln_node_port, btc_addr=ln_node_btc_addr)
        ln_nodes[node.name] = ln_node

    return ln_nodes


def create_basic_scenario(client):
    # Get all nodes
    btc_containers = [container for container in client.containers.list("all") if 'btc_n' in container.name]

    # Give every node some bitcoins to start with
    create_onchain_setup(client, btc_containers)

    # Run the LN nodes on top of bitcoind
    ln_nodes = deploy_ln_nodes(btc_containers)

    for node in ln_nodes.values():
        print node.toString()


if __name__ == '__main__':
    # Create docker client
    client = docker.from_env()

    # Configure logging
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO, handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ])

    create_basic_scenario(client)