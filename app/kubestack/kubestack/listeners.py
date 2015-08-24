import gear

class GearmanClient(gear.Client):
    def __init__(self, host, port):
        super(GearmanClient, self).__init__(client_id='kubestack')
        self.host = host
        self.port = port

    def connect(self):
        self.addServer(self.host, self.port)
        self.waitForServer()

    # return demand from gearman
    def getDemand(self):
        demand = []
        for connection in self.active_connections:
            try:
                req = gear.StatusAdminRequest()
                connection.sendAdminRequest(req)
            except Exception:
                self._lostConnection(connection)
                continue

            # demand comes in the format build:function:node_type
            for line in req.response.split('\n'):
                parts = [x.strip() for x in line.split('\t')]
                # parts[0] - function name
                if not parts or parts[0] == '.':
                    continue
                if not parts[0].startswith('build:'):
                    continue
                function = parts[0][len('build:'):]
                if ':' in function:
                    fparts = function.split(':')
                    # fparts[0] - function name
                    # fparts[1] - target node (type)
                    node_type = fparts[1]
                    demand.append(node_type)

        # just returns a list with all the labels needed
        return demand                
