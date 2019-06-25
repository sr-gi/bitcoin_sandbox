# Use the official Ubuntu 16.04 as a parent image.
FROM ubuntu:16.04

# Update the package list and install software properties common.
RUN apt-get update && apt-get install -y software-properties-common autoconf automake build-essential git libtool libgmp-dev libsqlite3-dev python python3 net-tools zlib1g-dev vim wget

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
WORKDIR /var/lib/bitcoin/
RUN chown bitcoin:bitcoin /var/lib/bitcoin/

# Switch to user bitcoin
USER bitcoin

# Set the working directory
RUN mkdir /var/lib/bitcoin/.bitcoin

# Export port 18443 (see bitcoin.conf)
EXPOSE 18443

# Copy bitcoin.conf to the container
ADD --chown=bitcoin:bitcoin bitcoin.conf /var/lib/bitcoin/.bitcoin/

###############
###  lnd   ###
##############

# Get lnd
RUN go get -d github.com/lightningnetwork/lnd

# Ask Sanket why he uses this particular commit
RUN cd go/src/github.com/lightningnetwork/lnd \
    && git checkout abfbdf6aec3bbf63a1f13e5706ee983efbfb4674 \
    && sed -i "s/.*defaultTrickleDelay.*=.*/        defaultTrickleDelay=2*1000/" config.go \
    && make \
    && make install

# Copy binaries
USER root
RUN cp go/bin/ln* /usr/bin/
USER bitcoin

# Export ports (see ln d.conf)
EXPOSE 9735 10009

# Create user folder and add conf file
RUN mkdir /var/lib/bitcoin/.lnd
ADD --chown=bitcoin:bitcoin lnd.conf /var/lib/bitcoin/.lnd/

