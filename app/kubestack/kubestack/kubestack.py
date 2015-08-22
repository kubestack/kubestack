# -*- coding: utf-8 -*-
import gear
import jenkins
import json
import sys
import time
import yaml

from kubeclient import KubeClient

from uuid import uuid4

class Kubestack():
    def __init__(self, configfile):
        self.configfile = configfile
        self.gearman = None
        self.jenkins = None
        self.kube    = None

        self.loadConfig()
        self.connectGearman()
        self.connectKube()

    # start the connection with gearman server
    def connectGearman(self):
        self.gearman = gear.Client()
        try:
            self.gearman.addServer(self.gearman_config['host'], self.gearman_config['port'])
            self.gearman.waitForServer()
        except:
            print "Error connecting to gearman server"
            sys.exit(1)

    # start the configuration with kubernetes
    def connectKube(self):
        try:
            self.kube = KubeClient(self.kubernetes_config['url'], token=self.kubernetes_config['api_key'])
        except Exception as e:
            print "Error connecting to Kubernetes"
            print str(e)
            sys.exit(1)

    # load configuration details
    def loadConfig(self):
        try:
            config = yaml.load(open(self.configfile))
        except Exception:
            error_message = "Error: cannot find configuration file %s" % self.configfile
            print error_message
            sys.exit(1)

        self.gearman_config = config.get('gearman-server', {})
        if not set(('host', 'port')).issubset(self.gearman_config):
            print "Gearman configuration is not properly set"
            sys.exit(1)

        self.jenkins_config = config.get('jenkins', {})
        if not set(('url', 'user', 'pass')).issubset(self.jenkins_config):
            print "Jenkins configuration is not properly set"
            sys.exit(1)

        self.kubernetes_config = config.get('kubernetes', {})
        if not set(('url', 'api_key')).issubset(self.kubernetes_config):
            print "Kuberentes configuration is not properly set"
            sys.exit(1)
