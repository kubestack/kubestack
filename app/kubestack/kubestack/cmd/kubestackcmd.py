# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Yolanda Robla'
__email__ = 'info@ysoft.biz'
__version__ = '0.1.0'

import argparse
import sys

from kubestack import kubestack

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
        pods = self.kubestack.kube.get(url='/pods')
        print self.kubestack.kube.get_json(pods)

    # create
    def create(self, pod_type):
        pass

    # delete
    def delete(self, pod_id):
        pass

def main():
    cmd = KubestackCmd()
    cmd.parse_arguments()
    return cmd.main()

if __name__ == "__main__":
    sys.exit(main())
