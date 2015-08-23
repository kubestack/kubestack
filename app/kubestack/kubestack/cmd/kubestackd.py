
# under the License.

import argparse
import daemon
import errno
import extras

# as of python-daemon 1.6 it doesn't bundle pidlockfile anymore
# instead it depends on lockfile-0.9.1 which uses pidfile.
pid_file_module = extras.try_imports(['daemon.pidlockfile', 'daemon.pidfile'])

import logging.config
import os
import sys
import signal
import traceback
import threading


class KubestackDaemon(object):
    def __init__(self):
        self.args = None

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description='KubeStack.')
        parser.add_argument('-c', dest='config',
                            default='/etc/kubestack/config.yaml',
                            help='path to config file')
        parser.add_argument('-d', dest='nodaemon', action='store_true',
                            help='do not run as a daemon')
        self.args = parser.parse_args()

    def exit_handler(self, signum, frame):
        self.kubestack.stop()

    def term_handler(self, signum, frame):
        os._exit(0)

    def main(self):
        import kubestack.kubestack
        self.kubestack = kubestack.kubestack.Kubestack(self.args.config)

        signal.signal(signal.SIGUSR1, self.exit_handler)
        signal.signal(signal.SIGTERM, self.term_handler)

        self.kubestack.start()

        while True:
            try:
                signal.pause()
            except KeyboardInterrupt:
                return self.exit_handler(signal.SIGINT, None)


def is_pidfile_stale(pidfile):
    """ Determine whether a PID file is stale.

        Return 'True' ("stale") if the contents of the PID file are
        valid but do not match the PID of a currently-running process;
        otherwise return 'False'.

        """
    result = False

    pidfile_pid = pidfile.read_pid()
    if pidfile_pid is not None:
        try:
            os.kill(pidfile_pid, 0)
        except OSError as exc:
            if exc.errno == errno.ESRCH:
                # The specified PID does not exist
                result = True

    return result


def main():
    kube = KubestackDaemon()
    kube.parse_arguments()

    pid = pid_file_module.TimeoutPIDLockFile('/var/run/kube.pid', 10)
    if is_pidfile_stale(pid):
        pid.break_lock()

    if kube.args.nodaemon:
        kube.main()
    else:
        with daemon.DaemonContext(pidfile=pid):
            kube.main()


if __name__ == "__main__":
    sys.exit(main())
