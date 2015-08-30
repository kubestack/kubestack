import json
import logging
import threading
import time
import zmq

# connects to zmq socket and listens to events
class ZMQClient(threading.Thread):
    log = logging.getLogger("kubestack.ZMQClient")
    watermark_sleep = 1

    def __init__(self, kube, host, port):
        threading.Thread.__init__(self, name='ZMQClient')
        self.host = host
        self.port = port
        self.zmq_context = zmq.Context()
        self.connect_socket()
        self._stopped = False
        self.kube = kube

    # method to connect to external zmq
    def connect_socket(self):
        self.socket = self.zmq_context.socket(zmq.SUB)
        event_filter = b''
        self.socket.setsockopt(zmq.SUBSCRIBE, event_filter)
        self.socket.RCVTIMEO = 5000
        final_url = "tcp://%s:%s" % (self.host, self.port)
        self.socket.connect(final_url)

    def check_socket_health(self):
        if not self.zmq_context or self.zmq_context.closed:
            self.zmq_context = zmq.Context()
        if not self.socket or self.socket.closed:
            self.connect_socket()

    def run(self):
        while not self._stopped:
            self.check_socket_health()
            try:
                m = self.socket.recv().decode('utf-8')
            except zmq.error.Again:
                continue

            # read event from zmq
            try:
                topic, data = m.split(None, 1)
                self.handleEvent(topic, data)
            except Exception as e:
                print str(e)
                self.log.exception("Exception handling job:")

    def stop(self):
        self._stopped = True

    def handleEvent(self, topic, data):
        # read event and listen for finished jobs
        args = json.loads(data)
        print args
        build = args['build']
        if 'node_name' not in build:
            return

        job_name = args['name']
        nodename = args['build']['node_name']

        if topic == 'onFinalized':
            # need to delete this pod
            self.kube.podCompleted(nodename)
