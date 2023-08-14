from docker_utils import *
from conf import *
import rpc_utils as bitcoin_cli
import logging
import time
import networkx as nx
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
    target_container, _ = run_new_nodes(client, 2)

    logging.info("  Getting info about existing nodes")
    logging.info("    Nodes are: {}".format(get_containers_names(client)))
    ip1 = get_ip_by_container_name(client, "btc_n1")
    ip2 = get_ip_by_container_name(client, "btc_n2")
    logging.info("    with ips: {}".format([ip2, ip1]))

    time.sleep(3)

    bitcoin_cli.addnode(target_container, ip2)


def create_scenario_from_graph(client, g):
    """
    Creates a network with the topology extracted from a graph.

    Warning: remember to call docker_setup with remove_existing=True or to set the names of the nodes so that they
    do not overlap with existing ones.

    :param client: docker client
    :param g: networkx graph
    :return:
    """

    # ToDo: Timers are meant to let bitcoind initialize. It will be good to implement it via signals instead
    # ToDo: That will imply (most likely) build a service based on debug.log parsing.

    logging.info("  Graph file contains {} nodes and {} connections".format(len(g.nodes()), len(g.edges())))

    containers = [run_new_node(client, node_num=node) for node in g.nodes()]

    time.sleep(10)

    for edge in g.edges():
        source = DOCK_CONTAINER_NAME_PREFIX + str(edge[0])
        dest = DOCK_CONTAINER_NAME_PREFIX + str(edge[1])
        source_container = client.containers.get(source)
        dest_container = client.containers.get(dest)

        bitcoin_cli.addnode(source_container, get_container_ip(dest_container))

    time.sleep(5)

    logging.info("  I have created {} nodes".format(len(containers)))

    num_connections = sum([len(bitcoin_cli.getpeerinfo(container)) for container in containers])/2
    logging.info("  I have created {} connections".format(num_connections))

    for container in containers:
        get_container_ip(container)


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
    logging.info("Creating scenario with a random topology: {} nodes and {} edges".format(num_nodes,
                                                                                          g.number_of_edges()))
    create_scenario_from_graph(client, g)


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
    if remove_existing:
        logging.info("  Removing existing containers")
        remove_containers(client)
    if create_docker_network:
        logging.info("  Creating network")
        create_network(client, overwrite_net=create_docker_network)
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
    create_scenario_from_graph_file(client, BITCOIN_GRAPH_FILE)

    # Scenario from a random graph:
    # create_scenario_from_er_graph(client, 5, 0.3)
