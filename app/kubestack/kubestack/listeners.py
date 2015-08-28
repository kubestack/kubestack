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
        needed_workers = {}
        job_worker_map = {}
        unspecified_jobs = {}

        for connection in self.active_connections:
            try:
                req = gear.StatusAdminRequest()
                connection.sendAdminRequest(req)
            except Exception:
                self._lostConnection(connection)
                continue

            # demand comes in the format build:function:node_type  total_jobs_queued  total_jobs_building  total_workers registered
            for line in req.response.split('\n'):
                parts = [x.strip() for x in line.split('\t')]
                # parts[0] - function name
                if not parts or parts[0] == '.':
                    continue
                if not parts[0].startswith('build:'):
                    continue
                function = parts[0][len('build:'):]

                # get total jobs in queue, including the ones being built
                try:
                    queued = int(parts[1])
                except:
                    queued = 0

                if ':' in function:
                    fparts = function.split(':')
                    job = fparts[-2]
                    worker = fparts[-1]
                    workers = job_worker_map.get(job, [])
                    workers.append(worker)
                    job_worker_map[job] = worker

                    # if there are queued tasks, add to demand
                    if queued > 0:
                        needed_workers[worker] = needed_workers.get(worker, 0) + queued
                elif queued > 0:
                    # job not specified
                    job = function
                    unespecified_jobs[job] = unspecified_jobs.get(job, 0) + queued

        # send demand of workers
        for job, queued in unspecified_jobs.items():
            workers = job_worker_map.get(job)
            if not workers:
                continue
            worker = workers[0]
            needed_workers[worker] = needed_workers.get(worker, 0) + queued

        return needed_workers
