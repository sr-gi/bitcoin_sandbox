# Use the official Ubuntu 14.04 as a parent image.
FROM ubuntu:14.04

# Update the package list and install software properties common.
RUN apt-get update && apt-get install -y software-properties-common autoconf automake build-essential git libtool libgmp-dev libsqlite3-dev python python3 net-tools zlib1g-dev

# Add bitcoind from the official PPA
RUN add-apt-repository --yes ppa:bitcoin/bitcoin && apt-get update

# Install bitcoind and make
RUN apt-get install -y bitcoind make

# Install additional packages
RUN apt-get install vim -y

# Install LN
RUN git clone https://github.com/ElementsProject/lightning.git

ADD --chown=bitcoin:bitcoin Makefile /lightning

RUN	cd lightning \
	&& ./configure \
	&& make install

# Set the working directory
WORKDIR /var/lib/bitcoin/
RUN chown bitcoin:bitcoin /var/lib/bitcoin/

# Switch to user bitcoin
USER bitcoin

# Set the working directory
RUN mkdir /var/lib/bitcoin/.bitcoin
RUN mkdir /var/lib/bitcoin/.lightning

# Export port 18443 (see bitcoin.conf)
EXPOSE 18443

# Copy bitcoin.conf to the container
ADD --chown=bitcoin:bitcoin bitcoin.conf /var/lib/bitcoin/.bitcoin/
ADD --chown=bitcoin:bitcoin config /var/lib/bitcoin/.lightning/