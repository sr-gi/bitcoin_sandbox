from btc_testbed.rpc_utils import *
from btc_testbed.docker_utils import *
from btc_testbed.conf import *

import logging
import time
import networkx as nx
import matplotlib.pyplot as plt


def create_basic_scenario(client):
    """
    Creates a basic network with 2 nodes and 1 connection from node 1 to node 2
    :param client: docker client
    :return:
    """

    logging.info("Creating basic scenario")
    logging.info("  Creating new nodes")
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
    logging.info(p1)
    logging.info(p2)


def create_scenario_from_graph(client, graph_file):
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

    # Plot graph
    # nx.draw(g)
    # plt.draw()
    # plt.show(block=True)

    logging.info("  Graph file contains {} nodes and {} connections".format(len(g.nodes()), len(g.edges())))

    for node in g.nodes():
        run_new_node(client, node_num=node)

    time.sleep(5)

    for edge in g.edges():
        print edge
        source = DOCK_CONTAINER_NAME_PREFIX + str(edge[0])
        dest = DOCK_CONTAINER_NAME_PREFIX + str(edge[1])
        r = rpc_create_connection(client, source, dest)
        print r

    time.sleep(5)

    logging.info("  I have created {} nodes".format(len(get_containers_names(client))))

    p0 = rpc_getpeerinfo(client, "btc_n0")
    p1 = rpc_getpeerinfo(client, "btc_n1")
    p2 = rpc_getpeerinfo(client, "btc_n2")
    num_connections = (len(p0) + len(p1) + len(p2))/2
    logging.info("  I have created {} connections".format(num_connections))

    return


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

    # Configure logging
    logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.DEBUG, handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ])

    # Create docker client & network
    client = docker_setup()

    # Create a scenario

    # Basic scenario: 2 nodes with 1 connection
    # create_basic_scenario(client)

    # Scenario from graph: gets topology from graph
    create_scenario_from_graph(client, TEST_GRAPH_FILE_1)

