# -*- coding: utf-8 -*-
import gear
import jenkins
import json
import listeners
import logging
import requests
import sys
import time
import threading
import yaml

from kubeclient import KubeClient

from uuid import uuid4

class Kubestack(threading.Thread):
    log = logging.getLogger("kubestack.Kubestack") 

    def __init__(self, configfile):
        threading.Thread.__init__(self, name='Kubestack')
        self.configfile = configfile
        self.jenkins = None
        self.kube    = None
        self.image   = None
        self._stopped = False
        self.watermark_sleep = 10
        self.demand_listeners = []

        self.loadConfig()
        self.connectKube()

    # stops thread properly
    def stop(self):
        self._stopped = True

    def _run(self):
        pass

    # main thread worker
    def run(self):
        while not self._stopped:
          try:
              for demand_listener in self.demand_listeners:
                  pods = demand_listener['object'].getDemand()
                  for pod in pods:
                      # create new nodes
                      self.createPod(pod, self.image)

              self._run()
          except Exception as e:
              print str(e)
              self.log.exception("Exception in main loop")
          time.sleep(self.watermark_sleep)

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

        if 'image' not in config:
            print "Docker image is not properly set"
            sys.exit(1)
        self.image = config.get('image')

        self.jenkins_config = config.get('jenkins', {})
        if not set(('url', 'user', 'pass')).issubset(self.jenkins_config):
            print "Jenkins configuration is not properly set"
            sys.exit(1)

        self.kubernetes_config = config.get('kubernetes', {})
        if not set(('url', 'api_key')).issubset(self.kubernetes_config):
            print "Kuberentes configuration is not properly set"
            sys.exit(1)

        # read demand listeners
        demand_listeners = config.get('demand-listeners', [])
        for listener in demand_listeners:
            if listener['type'] == 'gearman':
                if not set(('host', 'port')).issubset(listener):
                    print "Gearman configuration is not properly set"
                    sys.exit(1)

                listener['object'] = listeners.GearmanClient(listener['host'], listener['port'])
                listener['object'].connect()

            # add demand listener
            self.demand_listeners.append(listener)

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

    # delete a given template
    def deletePodTemplate(self, template_id):
        status = self.kube.delete(url='/podtemplates/%s' % template_id)
        return status

    # create a pod for a slave with the given label and image
    def createPod(self, label, image):
        pod_id = "jenkins-slave-%s" % uuid4()
        pod_content = {
            "kind": "Pod",
            "apiVersion": "v1",
            "metadata": {
                "name": pod_id,
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
        result = self.kube.post(url='/pods', json=pod_content)
        return result

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
