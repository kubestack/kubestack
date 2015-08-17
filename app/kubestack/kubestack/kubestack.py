# -*- coding: utf-8 -*-
import gear
import jenkins
import json
import sys
import time
import yaml

from uuid import uuid4

class Kubestack():
    def __init__(self, configfile, job):
        self.configfile = configfile
        self.job = job
        self.jobs = {}
        self.gearman = None
        self.jenkins = None

        self.loadConfig()
        self.connectGearman()
        self.connectJenkins()
        self.launchJob()

    # start the connection with gearman server
    def connectGearman(self):
        self.gearman = gear.Client()
        try:
            self.gearman.addServer(self.gearman_server, self.gearman_port)
            self.gearman.waitForServer()
        except:
            print "Error connecting to gearman server"
            sys.exit(1)

    # load configuration details
    def loadConfig(self):
        try:
            config = yaml.load(open(self.configfile))
        except Exception:
            error_message = "Error: cannot find configuration file %s" % self.configfile
            print error_message
            sys.exit(1)

        self.gearman_server = config.get('gearman-server', '127.0.0.1')
        self.gearman_port = config.get('gearman-port', 4730)

        self.jenkins_config = config.get('jenkins', {})
        if not set(('url', 'user', 'pass')).issubset(self.jenkins_config):
            print "Jenkins configuration is not properly set"
            sys.exit(1)
