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
            gobject introspection enabled Gegl not installed on this system -
            this package won't work as is.

            Ensure you have installed:
                pygobject,
                a recent gegl build with geobject introspection installed

                Package not installed!

            """)
        sys.exit(1)

with open('README.rst') as file:
    long_description = file.read()

setup(name = 'python-gegl',
      version = '0.1',
      author = 'João S. O. Bueno',
      author_email = 'gwidion@gmail.com',
      url = 'https://github.com/jsbueno/python-gegl',
      description = "Wrappers to simplify GEGL usage with python",
      package_dir = {'': 'gegl'},
      packages = [''],
      long_description = long_description,
      download_url = 'https://github.com/jsbueno/python-gegl/archive/v0.1.tar.gz',
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
