# Use the official Ubuntu 16.04 as a parent image.
FROM ubuntu:16.04

# Update the package list and install software properties common.
RUN apt-get update && apt-get install -y software-properties-common autoconf automake build-essential git libtool \
libgmp-dev libsqlite3-dev python python3 net-tools zlib1g-dev vim wget curl

# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py

# Install go
RUN wget https://dl.google.com/go/go1.11.5.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.11.5.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

###############
## bitcoind ##
##############

# Add bitcoind from the official PPA
RUN add-apt-repository --yes ppa:bitcoin/bitcoin && apt-get update

# Install bitcoind
RUN apt-get install -y bitcoind

# Set the working directory
WORKDIR /root

# Copy bitcoin.conf to the container
RUN mkdir .bitcoin
ADD bitcoin.conf .bitcoin/

# Export port 18443 (see bitcoin.conf)
EXPOSE 18443

# Copy bitcoin.conf to the container
ADD bitcoin.conf .bitcoin/

###############
###  lnd   ###
##############

# Get lnd
RUN go get -d github.com/lightningnetwork/lnd

RUN cd go/src/github.com/lightningnetwork/lnd \
    && make \
    && make install

# Copy binaries
RUN cp go/bin/ln* /usr/bin/

# Export ports (see lnd.conf)
EXPOSE 9735 10009

# Create user folder and add conf file
RUN mkdir .lnd
ADD lnd.conf .lnd/


