##############################################################################
#
# Copyright (c) 2010 Koansys, LLC..
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.koansys.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
try:
    import subprocess
    has_subprocess = True
except:
    has_subprocess = False

from distutils.cmd import Command

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

__version__ = '0.5.0'

requires = [
    'colander',
    'coverage',
    'deform',
    'mock',
    'nose',
    'pymongo',
    'pyramid',
    ]


class doc(Command):
    description = "generate or test documentation"
    user_options = [("test", "t",
                     "run doctests instead of generating documentation")]
    boolean_options = ["test"]

    def initialize_options(self):
        self.test = False

    def finalize_options(self):
        pass

    def run(self):
        if self.test:
            path = "doc/_build/doctest"
            mode = "doctest"
        else:
            path = "doc/_build/%s" % __version__
            mode = "html"

            # shutil.rmtree("doc/_build", ignore_errors=True)
            try:
                os.makedirs(path)
            except:
                pass

        if has_subprocess:
            status = subprocess.call(["sphinx-build", "-b", mode, "doc", path])

            if status:
                raise RuntimeError("documentation step '%s' failed" % mode)

            print ("")
            print (("Documentation step '%s' performed, results here:" % mode))
            print (("   %s/" % path))
        else:
            print ("""
`setup.py doc` is not supported for this version of Python.

Please ask in the user forums for help.
""")

setup(name='lumin',
      version=__version__,
      description='A library to aid in using MongoDB with repoze.bfg',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Topic :: Database",
        "Development Status :: 4 - Beta",
        "Framework :: BFG",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        ],
      keywords='',
      author="Koansys, LLC",
      author_email="info@koansys.org",
      url="http://koansys.org",
      license="BSD-derived (http://koansys.com/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require=requires,
      install_requires=requires,
      test_suite="nose.collector",
      cmdclass={'doc': doc},
      # entry_points="""\
      #   [nose.plugins.0.10]
      #   #mongodb = lumin.tests.mongodb:MongoDBPlugin
      # """
      )

