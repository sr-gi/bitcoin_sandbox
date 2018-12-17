# Use the official Ubuntu 14.04 as a parent image.
FROM ubuntu:14.04

# Update the package list and install software properties common.
RUN apt-get update && apt-get install -y software-properties-common

# Add bitcoind from the official PPA
RUN add-apt-repository --yes ppa:bitcoin/bitcoin && apt-get update

# Install bitcoind and make
RUN apt-get install -y bitcoind make

# Install additional packages
RUN apt-get install vim -y

# Switch to user bitcoin
USER bitcoin

# Set the working directory
WORKDIR /home/bitcoin

# Export port 18443 (see bitcoin.conf)
EXPOSE 18443

# Copy bitcoin.conf to the container
ADD --chown=bitcoin:bitcoin bitcoin.conf /home/bitcoin/.bitcoin/
