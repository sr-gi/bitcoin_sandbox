# Bitcoin test environment guide

## Deployment

### Create the test environment image

From the btc_testbed directory run:

`docker build -t btc_testbed .`

### Create nodes (by deploying docker containers)
`docker run -dit --name btc_nN bitcoind`

replace `nN` with the name of the node (n1, n2, n3, etc.). 

## Execution

### Log into a container

`docker exec -it btc_nM bash`

### Run an RPC command

To execute an RPC command to node `N` we will run:

`bitcoin-cli -rpcconnect=172.17.0.2+N command`

If your bitcoin.conf file is not set in the default directory in your host machine you may need to specify the location when running `bitcoin-cli`:

`bitcoin-cli -conf=path_to_conffile -rpcconnect=172.17.0.2+N command`

### Connect two nodes

If we want to connect node `nA` with node `nB`, we will run either:

`bitcoin-cli -rpcconnect=172.17.0.2+A addnode ip_nB onetry`

or

`bitcoin-cli -rpcconnect=172.17.0.2+B addnode ip_nA onetry`

### Disconnect two nodes

To disconnect node `nA` from node `nB` we can either run:

`bitcoin-cli -rpcconnect=172.17.0.2+A disconnectnode ip_nB`

or

`bitcoin-cli -rpcconnect=172.17.0.2+B disconnectnode ip_nA`

### Get network info

If we want to obtain the network information of a certain node `nC` (to check for example the number of peers of the given node) we can run:

`bitcoin-cli -rpcconnect=172.17.0.2+C getnetworkinfo`

### Get peers info

Same as before but for extended information about the peers:

`bitcoin-cli -rpcconnect=172.17.0.2+C getpeerinfo`

## Tools

We can use `create_node` tool to easily create a node by running:

`./create_node N`

Where N will be the identifier of the node, that it, the node will be called `btc_nN`.

## Build the network

### Create a seed node

We start by creating a seed node to whom every other node is going to be connected. The reason behind that will be explained later on.

`docker run -dit --name btc_seed btc_testbed`

### Generate an address we control

Now, we will generate 101 blocks in that node to an address we control. We can create it using `bitcoin_tools` (`python key_management.py`). In our case we are going to use the address `msfBL8TMzx1BSE9kTa1ThFJ3HjoAcPUSq3` that we have previously created.

### Generate 101 blocks to that address

`bitcoin-cli -rpcconnect=172.17.0.2 generatetoaddress 101 msfBL8TMzx1BSE9kTa1ThFJ3HjoAcPUSq3`

This address now holds the reward of 101 blocks (we will be able to use only the reward of the first one to create transactions since 100 blocks have to be waited before the coinbase transaction of a block can be redeemed). Moreover, we have one node that is aware of all the 101 blocks generated so far. This node will act as a seed for the initial blockchain state. We will connect every new generated node to the seed in order to bootstrap node easily.

While a traditional permissionless blockchain should never be bootstrap like that, this makes complete sense for the type of experiments we aim to run. Later on, we will need to send several transactions to the whole network, so a shared state in required with some address holding value.







