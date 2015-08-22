# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Yolanda Robla'
__email__ = 'info@ysoft.biz'
__version__ = '0.1.0'

import argparse
import sys

from kubestack import kubestack
from prettytable import PrettyTable

class KubestackCmd(object):
    def __init__(self):
        self.args = None

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description='Kubestack')
        parser.add_argument('-c', dest='config',
                            default='/etc/kubestack/config.yaml',
                            help='path to config file')

        subparsers = parser.add_subparsers(title='commands',
                                           description='valid commands',
                                           dest='command',
                                           help='additional help')

        cmd_list = subparsers.add_parser('list', help='list pods')
        cmd_list.set_defaults(func=self.list)

        cmd_delete = subparsers.add_parser(
            'delete',
            help='delete a pod')
        cmd_delete.set_defaults(func=self.delete)
        cmd_delete.add_argument('id', help='pod id')

        cmd_create = subparsers.add_parser(
            'create',
            help='create a pod')
        cmd_create.set_defaults(func=self.create)
        cmd_create.add_argument('type', help='pod type')

        self.args = parser.parse_args()

    def main(self):
        self.kubestack = kubestack.Kubestack(self.args.config)
        self.args.func()

    # list pods
    def list(self, labels = []):
        t = PrettyTable(["ID", "Name", "Labels", "Created"])
        t.align = 'l'

        pods = self.kubestack.kube.get(url='/pods')
        pod_list = self.kubestack.kube.get_json(pods)
        for pod_item in pod_list['items']:
            t.add_row([pod_item['metadata']['uid'], pod_item['metadata']['name'],
                       pod_item['metadata']['labels'], pod_item['metadata']['creationTimestamp']])
        print t

    # create
    def create(self, pod_type):
        pass

    # delete
    def delete(self):
        status = self.kubestack.kube.delete(url='/pods/%s' % self.args.id)
        if status.status_code == 200:
            print "Pod %s deleted successfully" % self.args.id
        else:
            print "Error on deleting. Status %s, error %s" % (status.status_code, status.reason)

def main():
    cmd = KubestackCmd()
    cmd.parse_arguments()
    return cmd.main()

if __name__ == "__main__":
    sys.exit(main())
