#!/usr/bin/python

import sys
from sets import Set
import cmdln
import json
import pprint
from jsonref import JsonRef

from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
from snap_interface import InterfaceCmd
from snap_leaf import LeafCmd

pp = pprint.PrettyPrinter(indent=2)
class ShowCmd(cmdln.Cmdln, CommonCmdLine):

    def __init__(self, parent, model, schema):

        cmdln.Cmdln.__init__(self)
        self.parent = parent
        self.model = model
        self.schema = schema

    def show(self, argv, all=False):
        # show command will work on various types of show
        # show all
        # show individual object
        # show individual object brief
        lastcmd = argv[-1] if all else argv[-2] if argv[-1] != 'brief' else argv[-3]
        l = LeafCmd(lastcmd, "show", self.parent, None, self.model, self.schema)

        # todo need to call the keys
        # l.do_lastcmd
        if not all:
            func = getattr(l, "do_%s" %(lastcmd,))
            func(argv[-2:])

        l.show_state(all=all)
