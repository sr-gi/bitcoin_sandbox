class LN_Node:
    def __init__(self, node_id, ip, port, btc_addr):
        self.id = node_id
        self.ip = ip
        self.port = port
        self.btc_addr = btc_addr

    def toString(self):
        return "(node_id: {}, ip: {}, port: {}, btc_addr: {})".format(
            str(self.id), str(self.ip), str(self.port), str(self.btc_addr)
        )
