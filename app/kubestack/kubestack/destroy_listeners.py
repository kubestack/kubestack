import threading
import zmq

# connects to zmq socket and listens to events
class ZMQClient(threading.Thread):
    def __init__(self, kube, host, port):
        threading.Thread.__init__(self, name='ZMQClient')
        self.zmq_context = zmq.Context()
        self.socket = self.zmq_context.socket(zmq.SUB)
        self.socket.RCVTIMEO = 1000
        event_filter = b''
        self.socket.setsockopt(zmq.SUBSCRIBE, event_filter)
        self.socket.connect('tcp://%s:%s' % (host, port))
        self._stopped = False
        self.kube = kube

    def run(self):
        while not self._stopped:
            try:
                m = self.socket.recv().decode('utf-8')
            except zmq.error.Again:
                continue

            # read event from zmq
            try:
                topic, data = m.split(None, 1)
                self.handleEvent(topic, data)
            except Exception:
                self.log.exception("Exception handling job:")

    def stop(self):
        self._stopped = True

    def handleEvent(self, topic, data):
        # read event and listen for finished jobs
        self.log.debug("ZMQ received: %s %s" % (topic, data))
        args = json.loads(data)
        build = args['build']
        if 'node_name' not in build:
            return

        job_name = args['name']
        nodename = args['build']['node_name']

        if topic == 'onFinalized':
            # need to delete this pod
            self.kube.podCompleted(nodename)
