from btc_testbed.conf import *

import docker
import socket
import logging


def get_containers_names(client, prefix=DOCK_CONTAINER_NAME_PREFIX):
    """
    Returns a list of container names.
    :param client: docker client
    :param prefix: string, prefix used in the containers names
    :return: list of strings with container names
    """
    return [container.name for container in client.containers.list("all") if prefix in container.name]


def count_containers(client, prefix=DOCK_CONTAINER_NAME_PREFIX):
    """
    Counts the number of existing containers with a given prefix in their name.
    :param client: docker client
    :param prefix: string, prefix used in the containers names
    :return: number of containers with the specified prefix
    """
    containers = get_containers_names(client)
    return sum([1 for c in containers if prefix in c])


def remove_container_by_name(client, container_name):
    """
    Removes a container given its name.
    :param client: docker client
    :param container_name: name of the container to remove.
    :return: boolean
    """
    try:
        client.containers.get(container_name).stop()
        return client.containers.get(container_name).remove()
    except docker.errors.NotFound as err:
        return False


def remove_containers(client, prefix=DOCK_CONTAINER_NAME_PREFIX):
    """
    Removes all containers with a given prefix.
    :param client: docker client
    :param prefix: string, prefix used in the containers names
    :return:
    """
    containers = get_containers_names(client)
    for c in containers:
        if prefix in c:
            remove_container_by_name(client, c)


def get_ip_by_container_name(client, container_name, network_name=DOCK_NETWORK_NAME):
    """
    Returns the ip of a given container (from its name)
    :param client: docker client
    :param container_name: name of the container
    :param network_name: docker network name
    :return: ip address
    """
    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound as err:
        return False

    return container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']


def is_valid_ip(addr):
    """
    Checks if an string is a valid IP
    :param addr: string to check
    :return: boolean, whether the string is a valid IP address.
    """
    try:
        socket.inet_aton(addr)
    except socket.error:
        return False
    return True


def get_ip_by_unknown(client, host):
    """
    Returns the ip of a container given its name or ip
    :param client: docker client
    :param host: container name or ip
    :return: ip address
    """
    if not is_valid_ip(host):
        # If it is not an ip, assume it's a container name:
        host = get_ip_by_container_name(client, host)
    return host


def run_new_node(client, network_name=DOCK_NETWORK_NAME, node_num=None):
    """
    Runs a new container.
    :param client: docker client
    :param network_name: docker network name
    :param node_num: node id
    :return:
    """
    containers = client.containers
    if node_num == None:
        c = count_containers(client) + 1
        name = DOCK_CONTAINER_NAME_PREFIX + str(c)
        port = {'18332/tcp': 22000 + c}
    else:
        name = DOCK_CONTAINER_NAME_PREFIX + str(node_num)
        port = {'18332/tcp': 22000 + node_num}

    containers.run(DOCK_IMAGE_NAME, "bitcoind", name=name, ports=port, detach=True, network=network_name)
    # containers.run("amacneil/bitcoin", "bitcoind", name=name, ports=port, detach=True, network=network_name)


def run_new_nodes(client, n):
    """
    Creates n containers.
    :param client: docker client
    :param n: number of containers to create
    :return:
    """
    for _ in range(n):
        run_new_node(client)


def create_network(client, network_name=DOCK_NETWORK_NAME, subnetwork=DOCK_NETWORK_SUBNET, gw=DOCK_NETWORK_GW):
    """
    Creates a docker network.
    :param client: docker client
    :param network_name: docker network name
    :return:
    """
    try:
        ipam_pool = docker.types.IPAMPool(subnet=subnetwork, gateway=gw)
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        client.networks.create(network_name, driver="bridge", ipam=ipam_config)
    except docker.errors.APIError as err:
        logging.info("    Warning: Network already exists")


def get_container_name_by_ip(client, ip, network_name=DOCK_NETWORK_NAME):
    """
    Returns the ip of a given container (from its name)
    :param client: docker client
    :param ip: ip address
    :param network_name: docker network name
    :return: docker container name if found, False otherwise.
    """

    # Sanity check IP formatting
    assert is_valid_ip(ip)

    # Get all the containers connected to the network
    containers = client.networks.get(network_name).containers

    # For each of the containers get the ip by name and check it with the provided ip.
    cont_name = False
    for container in containers:
        if ip == get_ip_by_container_name(client, container.name):
            cont_name = str(container.name)

    return cont_name
