# The cli is a cisco like cli which uses json schemas to build the cli tree based on the flexswitch generated json model objects.
# The cli will be installed under /user/local/python2.7/dist-packages, thus to run you must adjust permissions accordingly.
# best to run as root.

# quick install
python setup.py install

# run cli for options
snap_cli -help
