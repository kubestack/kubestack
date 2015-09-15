# Kubestack - Jenkins container nodes using Kubernetes

This project is a tool that allows to use dynamic jenkins slaves,
based on containers, relying on a Kubernetes cluster.

You will see three directories here:

* app:: it contains the main kubestack application
* ansible:: sample ansible roles and documentation, to spin up a kubernetes
cluster on OpenStack
* images:: Dockerfile and scripts used to generate the base image for this project

## Setup

### Create kubestack config file /etc/kubestack/config.yaml:

```yaml
demand-listeners:
    - name: gearman-server
      type: gearman
      host: xx.xx.xx.xx
      port: 4730

destroy-listeners:
    - name: zmq
      type: zmq
      host: xx.xx.xx.xx
      port: 8888

jenkins:
    external_url: 'http://jenkins_url'
    internal_url: 'http://xx.xx.xx.xx'
    user: jenkins
    pass: jenkins
kubernetes:
    url: 'http://xx.xx.xx.xx:8080'
    api_key: key
image: yrobla/jenkins-slave-swarm-infra:latest
```

### Run kubestack

python kubestack/cmd/kubestackd.py -d
