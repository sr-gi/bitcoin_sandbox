from bitcoin_sandbox.rpc_utils import *
from bitcoin_sandbox.docker_utils import *
from bitcoin_sandbox.conf import *
import logging
import time
import networkx as nx
import matplotlib.pyplot as plt
from sys import argv
from getopt import getopt


def create_basic_scenario(client):
    """
    Creates a basic network with 2 nodes and 1 connection from node 1 to node 2
    :param client: docker client
    :return:
    """

    logging.info("Creating basic scenario")
    logging.info("  Creating 2 new nodes")
    run_new_nodes(client, 2)

    logging.info("  Getting info about existing nodes")
    logging.info("    Nodes are: {}".format(get_containers_names(client)))
    ip1 = get_ip_by_container_name(client, "btc_n1")
    ip2 =  get_ip_by_container_name(client, "btc_n2")
    logging.info("    and have ips {} and {}".format(ip1, ip2))

    time.sleep(3)

    rpc1 = rpc_test_connection(client, "btc_n1")
    logging.info("  Testing rpc connection: {}".format(rpc1))

    c1 = rpc_create_connection(client, "btc_n1", "btc_n2")
    logging.info("  Creating a connection: {}".format(c1))

    time.sleep(3)

    logging.info("  Checking the connection")
    p1 = rpc_getpeerinfo(client, "btc_n1")
    p2 = rpc_getpeerinfo(client, "btc_n2")
    logging.info("    " + str(p1))
    logging.info("    " + str(p2))


def create_scenario_from_graph(client, g):
    """
    Creates a network with the topology extracted from a graph.

    Warning: remember to call docker_setup with remove_existing=True or to set the names of the nodes so that they
    do not overlap with existing ones.

    :param client: docker client
    :param g: networkx graph
    :return:
    """

    # Plot graph
    # nx.draw(g)
    # plt.draw()
    # plt.show(block=True)

    logging.info("  Graph file contains {} nodes and {} connections".format(len(g.nodes()), len(g.edges())))

    for node in g.nodes():
        run_new_node(client, node_num=node)

    time.sleep(5)

    for edge in g.edges():
        source = DOCK_CONTAINER_NAME_PREFIX + str(edge[0])
        dest = DOCK_CONTAINER_NAME_PREFIX + str(edge[1])
        r = rpc_create_connection(client, source, dest)

    time.sleep(5)

    logging.info("  I have created {} nodes".format(len(get_containers_names(client))))

    containers = get_containers_names(client)
    num_connections = sum([len(rpc_getpeerinfo(client, c)) for c in containers])/2
    logging.info("  I have created {} connections".format(num_connections))

    return


def create_scenario_from_graph_file(client, graph_file):
    """
    Creates a network with the topology extracted from a graphml file.

    Warning: remember to call docker_setup with remove_existing=True or to set the names of the nodes so that they
    do not overlap with existing ones.

    :param client: docker client
    :param graph_file: .graphml file with the network topology
    :return:
    """
    logging.info("Creating scenario from graph file")
    g = nx.read_graphml(graph_file, node_type=int)
    create_scenario_from_graph(client, g)


def create_scenario_from_er_graph(client, num_nodes, p):
    """
    Creates a random network using an erdos-renyi model.

    :param client: docker client
    :param num_nodes: number of nodes
    :param p: probability of a connection to be created
    :return:
    """

    g = nx.erdos_renyi_graph(num_nodes, p, directed=True)
    logging.info("Creating scenario with a random topology: {} nodes and {} edges".format(num_nodes, g.number_of_edges()))
    create_scenario_from_graph(client, g)


def run_scenario_vic1(client):

    ########################################
    # PART 1
    ########################################

    # Create scenario from graph
    create_scenario_from_graph_file(client, "./graphs/basic4.graphml")

    # Show node 0 balance and block info
    blocks_0_prev = rpc_getinfo(client, "btc_n0")["blocks"]
    balance_0_prev = rpc_call(client, "btc_n0", "getbalance")
    logging.info("  Node 0 is aware of {} blocks and has a balance of {} tbtc".format(blocks_0_prev, balance_0_prev))

    # Node 0 mines 101 blocks
    logging.info("  Node 0 is mining...")
    generate_0 = rpc_call(client, "btc_n0", "generate", arguments="101")

    # Show node 0 balance and block info
    blocks_0_after = rpc_getinfo(client, "btc_n0")["blocks"]
    balance_0_after = rpc_call(client, "btc_n0", "getbalance")
    logging.info("  Node 0 is aware of {} blocks and has a balance of {} tbtc".format(blocks_0_after, balance_0_after))

    # Show node 3 block info
    blocks_3 = rpc_getinfo(client, "btc_n3")["blocks"]
    logging.info("  Node 3 is aware of {} blocks".format(blocks_3))

    ########################################
    # PART 2
    ########################################

    # Print current connections
    logging.info("  btc_n0 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n0")))
    logging.info("  btc_n1 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n1")))
    logging.info("  btc_n2 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n2")))
    logging.info("  btc_n3 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n3")))

    # Connection between 2 and 3 dissapears
    logging.info("  Disconnecting nodes 2 and 3...")
    #disconnect = rpc_call(client, "btc_n2", "addnode", arguments="'172.192.1.4', 'remove'")
    disconnect = rpc_call(client, "btc_n2", "disconnectnode", arguments="'172.192.1.4'")
    time.sleep(5)

    # Print current connections
    logging.info("  btc_n0 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n0")))
    logging.info("  btc_n1 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n1")))
    logging.info("  btc_n2 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n2")))
    logging.info("  btc_n3 has peers: {}".format(rpcp_get_peer_ips(client, "btc_n3")))

    # Node 0 mines a block
    generate_0 = rpc_call(client, "btc_n0", "generate", arguments="1")
    blocks_0_dis = rpc_getinfo(client, "btc_n0")["blocks"]
    logging.info("  Node 0 is aware of {} blocks".format(blocks_0_dis))
    blocks_2_dis = rpc_getinfo(client, "btc_n2")["blocks"]
    logging.info("  Node 2 is aware of {} blocks".format(blocks_2_dis))
    blocks_3_dis = rpc_getinfo(client, "btc_n3")["blocks"]
    logging.info("  Node 3 is aware of {} blocks".format(blocks_3_dis))

    ########################################
    # PART 3 - Let's create a fork!
    ########################################


def docker_setup(build_image=True, create_docker_network=True, remove_existing=True):
    """
    Creates the docker client and optionally:
        - builds docker image
        - creates docker network
        - removes containers from previous deployments

    :param build_image: boolean, whether to build the image
    :param create_docker_network: boolean, whether to create the docker network
    :param remove_existing: boolean, whether to remove already existing containers
    :return: docker client
    """

    logging.info('Setting up docker client')
    client = docker.from_env()
    if build_image:
        logging.info("  Building docker image")
        client.images.build(path=".", tag=DOCK_IMAGE_NAME)
    if create_docker_network:
        logging.info("  Creating network")
        create_network(client)
    if remove_existing:
        logging.info("  Removing existing containers")
        remove_containers(client)
    return client


if __name__ == '__main__':

    if len(argv) > 1:
        # Get params from call
        _, args = getopt(argv, ['nobuild', 'nonet'])
        build = False if '--nobuild' in args else True
        network = False if '--nonet' in args else True
        remove = False if '--noremove' in args else True
    else:
        build = True
        network = True
        remove = True

    # Configure logging
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO, handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ])

    # Create docker client & network
    client = docker_setup(build_image=build, create_docker_network=network, remove_existing=remove)

    # Create a scenario

    # Basic scenario: 2 nodes with 1 connection
    # create_basic_scenario(client)

    # Scenario from graph: gets topology from graph
    create_scenario_from_graph_file(client, TEST_GRAPH_FILE_1)

    # Scenario from a random graph:
    # create_scenario_from_er_graph(client, 5, 0.3)

    # run_scenario_vic1(client)
