![bitcoin_tools](https://srgi.me/assets/images/bitcoin_sandbox_logo.png)

# Bitcoin sandbox guide

bitcoin_sandbox is a dockerized environment to create bitcoin (and lightning) networks for educational, research and 
testing purposes. Docker containers are used to run bitcoin nodes (with `bitcoind`) and lightning nodes (with `lnd`), 
which are in turn connected within each other to create the P2P network.

The tool allows three different alternatives to specify the connections between each node (that is, the Bitcoin network): 
* Deterministically, by manually specifying the connections in the source code.
* Deterministically, by loading a graph file that describes the connections.
* Randomly, by generating an erdos renyi graph with the given parameters (number of nodes and probability of creating
a connection between any two nodes). 

## Installation

1. Download / clone the repository.
2. Copy / rename `sample_conf.py` to `conf.py`. You can leave the default configuration values or tune them 
 to adjust your preferences. 
3. Install all the dependencies (`pip install -r requirements.txt`).

## Running the testbed

The ln branch builds on top of the deployment of the master branch (i.e. must be run after running `run_scenarios.py`)

If you haven't deployed the onchain scenario, check [Running the testbed in master.](https://github.com/sr-gi/bitcoin_sandbox/blob/master/README.md#running-the-testbed)

Once deployed, you can run the lightning network scenario by running:

`python run_ln_scenarios.py`

The LN scenarios are loaded from a `graphml` file and should match the number of nodes in the `run_scenarios` 
(`basic3_ln.graphml` is used by default). An instance of `lnd` will be deployed on each container.

Channels are open matching the connections in the graph file, using the property `weight` (`<data key="weight">x</data>`)
to define the channel capacity. If no `weight` is defined, `DEFAULT_LN_GRAPH_WEIGHT` is used (defined in `conf.py`)

## Connecting to the containers

Running containers can be seen also from docker:

`docker ps`

(container names will be, by default, `btc_ni`, with i an integer denoting their id).

### Log into a container

You can execute bash inside one of the containers with:

`docker exec -it btc_ni /bin/bash`