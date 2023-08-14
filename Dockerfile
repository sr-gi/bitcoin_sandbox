# Use the official Ubuntu 16.04 as a parent image.
FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install software properties common.
#RUN apt-get update && apt-get install -y software-properties-common autoconf automake build-essential git libtool \
#libgmp-dev libsqlite3-dev python python3 net-tools zlib1g-dev vim wget curl
RUN apt-get update && apt-get install -y software-properties-common vim curl python python3 python3-pip wget 

# Install pip
# RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
# RUN python3 get-pip.py

###############
## bitcoind ##
##############

RUN wget https://bitcoincore.org/bin/bitcoin-core-25.0/bitcoin-25.0-x86_64-linux-gnu.tar.gz \
    && tar -xzf bitcoin-25.0-x86_64-linux-gnu.tar.gz --strip-components=1

# Set the working directory
WORKDIR /root

# Copy bitcoin.conf to the container
RUN mkdir .bitcoin
ADD bitcoin.conf .bitcoin/

# Export port 18443 (see bitcoin.conf)
EXPOSE 18443

# Copy bitcoin.conf to the container
ADD bitcoin.conf .bitcoin/
