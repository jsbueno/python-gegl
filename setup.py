# coding: utf-8
# python-gegl installer
# Author: João S. O. Bueno

import sys
from distutils.core import setup

if "install" in sys.argv:
    try:
        from gi.repository import Gegl
    except ImportError:
        import sys
        sys.stderr.write("""\
            gobject introspection enabled GEGL not installed on this system -
            this package won't work as is.

            Ensure you have installed:
                pygobject,
                a recent GEGL build with gobject introspection installed

                Package not installed!

            \n""")
        sys.exit(1)

with open('README') as file:
    long_description = file.read()

setup(name = 'python-gegl',
      version = '0.2.1',
      author = 'João S. O. Bueno',
      author_email = 'gwidion@gmail.com',
      url = 'https://github.com/jsbueno/python-gegl',
      description = "Wrappers to simplify GEGL usage with python",
      packages = ['gegl'],
      long_description = long_description,
      download_url = 'https://github.com/jsbueno/python-gegl/releases/download/v0.2/v0.2.tar.gz',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2',
          'Topic :: Multimedia :: Graphics',
          'Topic :: Software Development :: Libraries',
          'Topic :: Printing',
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        ],
      license = "LGPL v3"

      )
