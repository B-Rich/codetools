#!/usr/bin/env python
#
# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.
#

"""
Code Analysis and Execution Tools

The CodeTools project includes packages that simplify meta-programming and
help the programmer separate data from code in Python. This library contains
classes that allow defining simple snippets, or "blocks", of Python code,
analyze variable dependencies in the code block, and use these dependencies to
construct or restrict an execution graph. These (restricted) code blocks can
then be executed in any namespace. However, this project also provides a
Traits-event-enhanced namespace, called a "context", which can be used in
place of a vanilla namespace to allow actions to be performed whenever
variables are assigned or retrieved from the namespace. This project is used
as the foundation for the BlockCanvas project.

Prerequisites
-------------
If you want to build CodeTools from source, you must first install 
`setuptools <http://pypi.python.org/pypi/setuptools/0.6c8>`_.

"""


from distutils import log
from distutils.command.build import build as distbuild
from make_docs import HtmlBuild
from pkg_resources import DistributionNotFound, parse_version, require, \
    VersionConflict
from setuptools import setup, Extension, find_packages
from setuptools.command.develop import develop
import os
import zipfile

# FIXME: This works around a setuptools bug which gets setup_data.py metadata
# from incorrect packages. Ticket #1592
#from setup_data import INFO
setup_data = dict(__name__='', __file__='setup_data.py')
execfile('setup_data.py', setup_data)
INFO = setup_data['INFO']

# Pull the description values for the setup keywords from our file docstring.
DOCLINES = __doc__.split("\n")


# Functions to generate docs from source during project builds.
def generate_docs():
    """ If sphinx is installed, generate docs.
    """
    doc_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'docs')
    source_dir = os.path.join(doc_dir, 'source')
    html_zip = os.path.join(doc_dir,  'html.zip')
    dest_dir = doc_dir

    required_sphinx_version = "0.4.1"
    sphinx_installed = False
    try:
        require("Sphinx>=%s" % required_sphinx_version)
        sphinx_installed = True
    except (DistributionNotFound, VersionConflict):
        log.warn('Sphinx install of version %s could not be verified.'
            ' Trying simple import...' % required_sphinx_version)
        try:
            import sphinx
            if parse_version(sphinx.__version__) < parse_version(
                required_sphinx_version):
                log.error("Sphinx version must be >=" + \
                    "%s." % required_sphinx_version)
            else:
                sphinx_installed = True
        except ImportError:
            log.error("Sphinx install not found.")

    if sphinx_installed:
        log.info("Generating %s documentation..." % INFO['name'])
        docsrc = source_dir
        target = dest_dir

        try:
            build = HtmlBuild()
            build.start({
                'commit_message': None,
                'doc_source': docsrc,
                'preserve_temp': True,
                'subversion': False,
                'target': target,
                'verbose': True,
                'versioned': False
                }, [])
            del build

        except:
            log.error("The documentation generation failed.  Falling back to "
                "the zip file.")

            # Unzip the docs into the 'html' folder.
            unzip_html_docs(html_zip, doc_dir)
    else:
        # Unzip the docs into the 'html' folder.
        log.info("Installing %s documentation from zip file.\n" % INFO['name'])
        unzip_html_docs(html_zip, doc_dir)

def unzip_html_docs(src_path, dest_dir):
    """ Given a path to a zipfile, extract its contents to a given 'dest_dir'.
    """
    file = zipfile.ZipFile(src_path)
    for name in file.namelist():
        cur_name = os.path.join(dest_dir, name)
        if not name.endswith('/'):
            out = open(cur_name, 'wb')
            out.write(file.read(name))
            out.flush()
            out.close()
        else:
            if not os.path.exists(cur_name):
                os.mkdir(cur_name)
    file.close()

class my_develop(develop):
    def run(self):
        develop.run(self)
        generate_docs()

class my_build(distbuild):
    def run(self):
        distbuild.run(self)
        generate_docs()


# Make the actual setup call.
setup(
    author = 'Enthought, Inc.',
    author_email = 'info@enthought.com',
    classifiers = [c.strip() for c in """\
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        Intended Audience :: Science/Research
        License :: OSI Approved :: BSD License
        Operating System :: MacOS
        Operating System :: Microsoft :: Windows
        Operating System :: OS Independent
        Operating System :: POSIX
        Operating System :: Unix
        Programming Language :: Python
        Topic :: Scientific/Engineering
        Topic :: Software Development
        Topic :: Software Development :: Libraries
        """.splitlines() if len(c.strip()) > 0],
    cmdclass = {
        'develop': my_develop,
        'build': my_build
    },
    dependency_links = [
        'http://code.enthought.com/enstaller/eggs/source',
        ],
    description = DOCLINES[1],
    include_package_data = True,
    install_requires = INFO['install_requires'],
    license = 'BSD',
    long_description = '\n'.join(DOCLINES[3:]),
    maintainer = 'ETS Developers',
    maintainer_email = 'enthought-dev@enthought.com',
    name = 'CodeTools',
    namespace_packages = [
        "enthought",
        ],
    packages = find_packages(),
    platforms = ["Windows", "Linux", "Mac OS-X", "Unix", "Solaris"],
    tests_require = [
        'nose >= 0.10.3',
        ],
    test_suite = 'nose.collector',
    url = 'http://code.enthought.com/projects/code_tools.php',
    version = INFO['version'],
    zip_safe = False,
    )

