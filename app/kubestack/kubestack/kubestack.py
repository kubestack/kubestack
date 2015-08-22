# -*- coding: utf-8 -*-
import gear
import jenkins
import json
import requests
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

    # returns a list of pods
    def getPods(self):
        pods = self.kube.get(url='/pods')
        pod_list = self.kube.get_json(pods)
        return pod_list

    # returns a list of pod templates
    def getPodTemplates(self):
        pod_templates = self.kube.get(url='/podtemplates')
        pod_template_list = self.kube.get_json(pod_templates)
        return pod_template_list

    # delete a given pod
    def deletePod(self, pod_id):
        status = self.kube.delete(url='/pods/%s' % pod_id)
        return status

    # create a template for a slave with the given label and image
    def createPodTemplate(self, label, image):
        template_id = "jenkins-slave-%s" % uuid4()
        template_content = {
            "kind": "PodTemplate",
            "apiVersion": "v1",
            "metadata": {
                "name": template_id,
                "labels": {
                    "name": "jenkins-slave-%s" % label,
                }
            },
            "template": {
                "metadata": {
                    "name": template_id,
                    "labels": {
                        "name": "jenkins-slave-%s" % label,
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "jenkins-slave-%s" % label,
                            "image": image,
                            "command": [
                                "sh",
                                "-c",
                                "/usr/local/bin/jenkins-slave.sh -master %s -username %s -password %s -executors 1 -labels %s" %
                                (self.jenkins_config['url'], self.jenkins_config['user'],
                                 self.jenkins_config['pass'], label)
                            ]
                        }
                    ]
                }
            }
        }
        result = self.kube.post(url='/podtemplates', json=template_content)
        return result