===============================
KubeStack
===============================

.. image:: https://img.shields.io/travis/yrobla/kubestack.svg
        :target: https://travis-ci.org/yrobla/kubestack

.. image:: https://img.shields.io/pypi/v/kubestack.svg
        :target: https://pypi.python.org/pypi/kubestack


Python app to manage dynamic Jenkins slaves with Kubernetes

* Free software: BSD license
* Documentation: https://kubestack.readthedocs.org.

Features
--------

* Creates dynamic jenkins slaves based on kubernetes

Configuration file needed on /etc/kubestack/config.yaml
-------------------------------------------------------
gearman-server:
    host: gearman_host
    port: 4730
jenkins:
    url: 'https://url.to.jenkins/'
    user: jenkins_user
    pass: jenkins_pass
kubernetes:
    url: 'http://url_to_kubernetes/'
    api_key: kubernetes_api_key

