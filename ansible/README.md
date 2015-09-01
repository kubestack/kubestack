# Kubernetes Ansible (for HP Cloud)

# based on https://github.com/GoogleCloudPlatform/kubernetes/tree/master/contrib/ansible

This project has the intention to give a set of recommendation and steps to deploy
kubernetes using ansible playbooks, on HP Cloud.

## Before starting

* Boot an instance on HP cloud to be used as master. Ensure that you add the meta "groups=masters" to it
* Boot an instance to be used as etcd server (often same as master, only one). Ensure that you add the meta
"groups=etcd" to the instance. If you share etcd with master, please add "groups=masters,etcd" to it.
* Boot as much instances on HP cloud as minions you need. Ensure that you add the meta "groups=nodes" to it.
* Make sure your ansible running machine has latest ansible running (with latest ansible-openstack addons), as
well as latest shade, os-client-config and python-netaddr installed.

## Setup

### Configure os-client-config

In order to use OpenStack dynamic inventory we rely on shade and os-client config. So we need to create a file
/etc/ansible/openstack.yml:

cache:
  max_age: 0
clouds:
  cloud_name:
    cloud: hp
    auth:
      username: hpcloud_username
      password: XXXX
      project_name: hpcloud_project_name
    region_name: hpcloud_region


### Configure Cluster options

Look though all of the options in `group_vars/all.yml` and
set the variables to reflect your needs. The options are described there
in full detail.

## Clone playbooks and add extra roles

Clone the playbooks from
https://github.com/GoogleCloudPlatform/kubernetes
and move to contrib/ansible

Be sure to update cluster.yml with the settings we need, and add
the resolution role to this file and to the repo.
As HP Cloud has no way to resolve the hostnames properly, this
role is adding the private ips of each instance into the related
ones. Please be sure to add all the instance names to instances_list
var.

## Running the playbook

After going through the setup, run the setup script provided:

`$ ./setup.sh`

You may override the inventory file by doing:

`INVENTORY=/opt/stack/ansible/contrib/inventory/openstack.py ./setup.sh`

Where that path points to Ansible OpenStack dynamic inventory.

In general this will work on very recent Fedora, rawhide or F21.  Future work to
support RHEL7, CentOS, and possible other distros should be forthcoming.

### Targeted runs

You can just setup certain parts instead of doing it all.

#### etcd

`$ ./setup.sh --tags=etcd`

#### Kubernetes master

`$ ./setup.sh --tags=masters`

#### kubernetes nodes

`$ ./setup.sh --tags=nodes`

### flannel

`$ ./setup.sh --tags=flannel`
