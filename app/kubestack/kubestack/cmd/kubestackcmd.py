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

        self.args = parser.parse_args()

    def main(self):
        self.kubestack = kubestack.Kubestack(self.args.config)

def main():
    cmd = KubestackCmd()
    cmd.parse_arguments()
    return cmd.main()

if __name__ == "__main__":
    sys.exit(main())
