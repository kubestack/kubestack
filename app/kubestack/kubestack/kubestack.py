# -*- coding: utf-8 -*-
import jenkins
import json
import listeners
import destroy_listeners
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
    POD_PREFIX = 'jenkins-slave'

    def __init__(self, configfile, start_listeners=True):
        threading.Thread.__init__(self, name='Kubestack')
        self.configfile = configfile
        self.jenkins_object = None
        self.kube    = None
        self.image   = None
        self._stopped = False
        self.watermark_sleep = 10
        self.demand_listeners = []
        self.destroy_listeners = []
        self.existing_pods = 0
        self.lock = threading.Lock()
        self.start_listeners = start_listeners

        self.loadConfig()
        self.connectKube()
        self.connectJenkins()

    # stops thread properly
    def stop(self):
        self._stopped = True

        # disconnect listeners
        for listener in self.destroy_listeners:
            listener['object'].stop()
            listener['object'].join()
            if listener['type'] == 'zmq':
                listener['object'].zmq_context.destroy()


    # main thread worker
    def run(self):
        while not self._stopped:
          try:
              for demand_listener in self.demand_listeners:
                  # it returns a dict with object:total_needed
                  pods = demand_listener['object'].getDemand()
                  for key, val in pods.items():
                      total_existing = self.getExistingPods()
                      current_demand = val - total_existing
                      # create all pods that we need
                      if current_demand > 0:
                          # create all the pods we need
                          for _ in range(current_demand):
                              self.createPod(key, self.image)

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

    # start the connection with jenkins
    def connectJenkins(self):
        try:
            self.jenkins_object = jenkins.Jenkins(self.jenkins_config['external_url'],
                username=self.jenkins_config['user'], password=self.jenkins_config['pass'])
        except Exception as e:
            print "Error connecting to Jenkins"
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
        if not set(('internal_url', 'external_url', 'user', 'pass')).issubset(self.jenkins_config):
            print "Jenkins configuration is not properly set"
            sys.exit(1)

        self.kubernetes_config = config.get('kubernetes', {})
        if not set(('url', 'api_key')).issubset(self.kubernetes_config):
            print "Kuberentes configuration is not properly set"
            sys.exit(1)

        # read demand listeners
        if self.start_listeners:
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

            #  read destroy listeners
            dlisteners = config.get('destroy-listeners', [])
            for listener in dlisteners:
                if listener['type'] == 'zmq':
                    if not set(('host', 'port')).issubset(listener):
                        print "ZMQ configuration is not properly set"
                        sys.exit(1)

                    listener['object'] = destroy_listeners.ZMQClient(self, listener['host'], listener['port'])
                    listener['object'].start()

                # add destroy listener
                self.destroy_listeners.append(listener)

    # returns a list of pods
    def getPods(self):
        pods = self.kube.get(url='/pods')
        pod_list = self.kube.get_json(pods)
        return pod_list

    # return the number of pods already in the system, locking access
    def getExistingPods(self):
        self.lock.acquire()
        number = self.existing_pods
        self.lock.release()
        return number

    # returns a list of pod templates
    def getPodTemplates(self):
        pod_templates = self.kube.get(url='/podtemplates')
        pod_template_list = self.kube.get_json(pod_templates)
        return pod_template_list

    # remove a jenkins node that starts with that id
    def deleteJenkinsNode(self, pod_id):
        nodes = self.jenkins_object.get_nodes()
        for node in nodes:
            if pod_id in node['name']:
                self.jenkins_object.delete_node(node['name'])
                return True
        return False

    # delete a given pod
    def deletePod(self, pod_id):
        # first remove from jenkins
        try:
            self.deleteJenkinsNode(pod_id)
        except Exception as e:
            self.log.debug("Exception removing from jenkins")
            print str(e)

        # remove from kube independent of the result of jenkins
        # if there was a failure on disconnect, when the node
        # is deleted, jenkins will remove that automatically
        # after a period of time
        try:
            self.lock.acquire()
            status = self.kube.delete(url='/pods/%s' % pod_id)
            self.existing_pods -= 1
            if self.existing_pods < 0:
                self.existing_pods = 0
            self.lock.release()
            return status
        except Exception as e:
            print str(e)
            self.log.debug("Exception in deleting pods")
            return False

    # handles completion of a pod
    def podCompleted(self, pod_id):
        # swarm concats a sufix at the end, we need to get rid of it
        fragments = pod_id.split('-')
        fragments.pop()
        self.deletePod('-'.join(fragments))

    # delete pods starting with a given label
    def deletePodsByLabel(self, label):
        pod_list = self.getPods()
        total_available = 0
        for pod_item in pod_list['items']:
            current_label = pod_item['metadata']['labels']['name']

            if label in current_label:
                # delete this pod
                self.deletePod(pod_item['metadata']['name'])

    # delete a given template
    def deletePodTemplate(self, template_id):
        status = self.kube.delete(url='/podtemplates/%s' % template_id)
        return status

    # create a pod for a slave with the given label and image
    def createPod(self, label, image):
        try:
            self.lock.acquire()
            pod_id = self.POD_PREFIX + "-%s" % uuid4()
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
                                (self.jenkins_config['internal_url'], self.jenkins_config['user'],
                                 self.jenkins_config['pass'], label)
                            ]
                        }
                    ]
                }
            }
            result = self.kube.post(url='/pods', json=pod_content)
            self.existing_pods += 1
            self.lock.release()
            return result
        except Exception as e:
            self.lock.release()
            print str(e)
            self.log.exception("Exception creating pod")
            return False

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
