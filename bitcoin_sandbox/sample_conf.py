# Copy this file with your own configuration and save it as conf.py

# Docker
DOCK_NETWORK_NAME = 'regtest_net'
DOCK_NETWORK_SUBNET = '172.192.1.0/24'
DOCK_NETWORK_GW = '172.192.1.1'
DOCK_CONTAINER_NAME_PREFIX = 'btc_n'
DOCK_IMAGE_NAME = 'sandbox_ln'

# Log
LOG_FILE = 'bitcoin_sandbox.log'

# Graphs
BITCOIN_GRAPH_FILE = './graphs/basic_mesh.graphml'
LN_GRAPH_FILE = './graphs/basic_ln.graphml'
DEFAULT_LN_GRAPH_WEIGHT = 10000

