#!/usr/bin/python

import sys
from sets import Set
import cmdln
import json
import pprint
from jsonref import JsonRef

from jsonschema import Draft4Validator
from commonCmdLine import CommonCmdLine
from snap_leaf import LeafCmd

pp = pprint.PrettyPrinter(indent=2)
class ShowCmd(cmdln.Cmdln, CommonCmdLine):

    def __init__(self, parent, model, schema):

        cmdln.Cmdln.__init__(self)
        self.objname = 'show'
        self.parent = parent
        self.model = model
        self.schema = schema
        self.configList = []

    def doesConfigExist(self, c):
        '''
        :param entry: CmdEntry
        :return: already provisioned CmdEntry or None if it does not exist
        '''
        for config in self.configList:
            if config.name == c.name:
                return config
        return None

    def show(self, argv, all=False):
        # show command will work on various types of show
        # show all
        # show individual object
        # show individual object brief
        lastcmd = argv[-1] if all else argv[-2] if argv[-1] != 'brief' else argv[-3]
        schemaname = self.getSchemaCommandNameFromCliName(lastcmd, self.model)
        # leaf will gather all the config info for the object
        l = LeafCmd(schemaname, lastcmd, "show", self, None, [self.model], [self.schema])
        l.applybaseconfig(lastcmd)

        # todo need to call the keys
        # l.do_lastcmd
        if not all:
            func = getattr(l, "do_%s" %(lastcmd,))
            func(argv[-2:])

        self.show_state(all=all)

    def show_state(self, all=False):

        configObj = self.getConfigObj()
        if configObj and configObj.configList:
            sys.stdout.write("Applying Show:\n")
            # tell the user what attributes are being applied
            for i in range(len(configObj.configList)):
                config = configObj.configList[-(i+1)]
                #config.show()

                # get the sdk
                sdk = self.getSdkShow()

                funcObjName = config.name
                try:
                    if all:
                        printall_func = getattr(sdk, 'print' + funcObjName + 'States')
                        printall_func()
                    else:
                        # update all the arguments so that the values get set in the get_sdk_...
                        print_func = getattr(sdk, 'print' + funcObjName + 'State')
                        data = config.getSdkConfig()
                        (argumentList, kwargs) = self.get_sdk_func_key_values(data, print_func)
                        print_func(*argumentList)

                    # remove the configuration as it has been applied
                    config.clear(None, None, all=True)
                except Exception as e:
                    sys.stdout.write("FAILED TO GET OBJECT for show state: %s\n" %(e,))
