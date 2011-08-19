import os
import subprocess
import sys
import tempfile

from nose.plugins import Plugin


class MongoDBPlugin(Plugin):
    """A nose plugin that setups a test managed mongodb instance.
    """

    def __init__(self):
        super(MongoDBPlugin, self).__init__()
        self.mongodb_bin = None
        self.db_port = None
        self.db_path = None
        self.process = None
        self._running = False
        self._enabled = False

    def options(self, parser, env={}):
        parser.add_option(
            "--mongodb-bin", action="store", dest="mongodb_bin", default=None,
            help="Setup a mongodb test instance using the specified binary.")
        parser.add_option(
            "--mongodb-port", action="store", dest="mongodb_port", type="int",
            default=43000, help="Port to run the test mongodb instance on")

    def configure(self, options, conf):
        if options.mongodb_bin:
            self.db_port = options.mongodb_port
            self.mongodb_bin = os.path.abspath(
                os.path.expanduser(os.path.expandvars(options.mongodb_bin)))

            self.enabled = True
            assert os.path.exists(self.mongodb_bin), "Invalid mongodb binary"

    def begin(self):
        """Start an instance of mongodb
        """
        self._running = False

        if "TEST_MONGODB" in os.environ:
            return

        # Stores data here
        self.db_path = tempfile.mkdtemp()
        if not os.path.exists(self.db_path):
            os.mkdir(self.db_path)

        # Another option of possible use.
        #"--noprealloc", # only needed on fs that don't sparse
        # allocate, ie. not (ext4, btrfs, xfs)

        self.process = subprocess.Popen(
            args=[
                self.mongodb_bin,
                "--dbpath",
                self.db_path,
                "--port",
                str(self.db_port),
                "--quiet",  # don't flood stdout, we're not reading it
                "--nohttpinterface",  # save the port
                "--noscripting",   # not used
                "--nounixsocket",   # not used
                "--noprealloc",
                ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
            )
        os.environ["TEST_MONGODB"] = "localhost:%s" % (self.db_port)
        self._running = True

    def finalize(self, result):
        """Stop the mongodb instance.
        """
        if not self._running:
            return

        del os.environ["TEST_MONGODB"]
        if sys.platform == 'darwin':
            self.process.kill()
        else:
            self.process.terminate()
        self.process.wait()
        self._running = False
