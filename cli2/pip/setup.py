from setuptools import setup, find_packages

setup(
    # Application name:
    name="snap_cli",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Corry Cordes",
    author_email="ccordes@snaproute.com",

    # Packages
    packages=find_packages(),
    
    # Additional data files
    package_data= {'snap_cli/schema' : 'snap_cli/schema/*.json',
                   'snap_cli/model/cisco'  : 'snap_cli/model/cisco/*.json',
    },

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="http://github.com/OpenSnaproute/apps/cli2",

    license="LICENSE.txt",
    description="Snaproute Inc Flexswitch CLI",

    # long_description=open("README.txt").read(),

    install_requires=['cmdln', 'jsonref', 'jsonschema', 'requests'],

    entry_points={"console_scripts": ["snap_cli = snap_cli:main"]}
)
