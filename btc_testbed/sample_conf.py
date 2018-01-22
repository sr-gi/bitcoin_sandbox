# Copy this file with your own configuration and save it as conf.py

DOCK_NETWORK_NAME = 'bitcoinnet'
DOCK_NETWORK_SUBNET ='172.192.1.0/24'
DOCK_NETWORK_GW = '172.192.1.254'
DOCK_CONTAINER_NAME_PREFIX = 'btc_n'
DOCK_IMAGE_NAME = 'btc_testbed'

BTC_RPC_PORT = 18332
BTC_RPC_USER = 'uab'
BTC_RPC_PASSWD = 'uabpassword'

LOG_FILE = 'btc_testbed.log'
TEST_GRAPH_FILE_1 = './graphs/basic3.graphml'