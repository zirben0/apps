#!/usr/lib/python
#
#Copyright [2016] [SnapRoute Inc]
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#
# _______  __       __________   ___      _______.____    __    ____  __  .___________.  ______  __    __
# |   ____||  |     |   ____\  \ /  /     /       |\   \  /  \  /   / |  | |           | /      ||  |  |  |
# |  |__   |  |     |  |__   \  V  /     |   (----` \   \/    \/   /  |  | `---|  |----`|  ,----'|  |__|  |
# |   __|  |  |     |   __|   >   <       \   \      \            /   |  |     |  |     |  |     |   __   |
# |  |     |  `----.|  |____ /  .  \  .----)   |      \    /\    /    |  |     |  |     |  `----.|  |  |  |
# |__|     |_______||_______/__/ \__\ |_______/        \__/  \__/     |__|     |__|      \______||__|  |__|
#
#
# This file contains code which generates a json schema for a given data model.  The imported json model assumes
# that some of the following keyword attributes are set.
#
#   'type' - int, bool, string
#   'isKey' - whether this attribute is a key, which will be used to make a leaf template
#   'isArray' - whether this attribute is a list or not
#   'description' - default description of the attribute
#   'default' - default values used for this attribute if isDefaultSet is set
#   'isDefaultSet' - used to know wehter the default value is valid or not
#   'position' - flexsdk api index value( not really used
#   'selections' - If there are any string or enumerated values which are selectable for the user
#
import json
import os, copy, sys, string
from optparse import OptionParser


GENERATED_SCHEMA_PATH = 'file:/tmp/snaproute/cli/schema/'
GENERATED_MODEL_PATH = 'file:/tmp/snaproute/cli/model/cisco/'

SUBCMD_TEMPLATE = {
}

def isboolean(v):
    return v.lower() in ('bool', 'boolean')

def isCommonType(t):
    return t.startswith('int') or t.startswith('uint') or t in ('string', 'bool', 'boolean', 'char')

class ModelLeafTemplate(object):
    '''
    Class containeer which will serve as a template for model class key attrbibutes
    which must be entered by a user
    '''
    def __init__(self,):
        # lets get the model name for use in the schema
        self.templateinfo = {
            "prompt": "", # empty string will not display anything
            "cliname": "",
            "value": {

            },
            "commands": {
            },
        }

    def getInfo(self):
        return self.templateinfo

    def setHelp(self, *args, **kwargs):
        pass

    def getMemberPropertiesPath(self):
        return self.templateinfo["value"]

    def getCommandPath(self):
        return self.templateinfo["commands"]

    def setDefault(self, attr, v):
        # the only required fields
        if attr in self.getMemberPropertiesPath():
            self.getMemberPropertiesPath()[attr] = v

    def setSubCommandRef(self, filename):
        '''
        This will hold the dynamic subcommand reference that users will need to update to mach
        the model.
        :param filename:
        :return:
        '''

        self.getCommandPath().update({
            "$ref": GENERATED_MODEL_PATH + filename
        })

    def setAdditionalShowCommands(self):
        self.leafmodel['commands'].update({
            "brief" : {
                "cliname": "brief",
            },
        })

    def setArgType(self, type, selections=None, min=None, max=None):

        def isnumeric(type):
            return type in defaultMinMaxDict.keys()

        defaultMinMaxDict = {
            'int8': (-128, 127),
            'int16': (32768, 32767),
            'int32': (-2147483648, 2147483647),
            'int64': (-9223372036854775808, 9223372036854775807),
            'uint8': (0, 255),
            'uint16': (0, pow(2,16)),
            'uint32': (0, pow(2,32)),
            'uint64': (0, pow(2,64)),
        }
        if 'argtype' in self.getMemberPropertiesPath():
            self.getMemberPropertiesPath()['argtype']["type"] = type
            if selections and ("SELECTION" or "selections" in selections):
                # selections should be separated by /
                s = selections.split('/')
                if isnumeric(type):
                    s = [x.split('(')[1].rstrip(')') for x in s]
                else:
                    s = [x.split('(')[0] for x in s]
                self.getMemberPropertiesPath()['argtype']["enum"] = s

            if isnumeric(type):
                if min is not None and max is not None:
                    self.getMemberPropertiesPath()['argtype']["minimum"] = string.atoi(min)
                    self.getMemberPropertiesPath()['argtype']["maximum"] = string.atoi(max)
                else:
                    self.getMemberPropertiesPath()[attr]["minimum"] = defaultMinMaxDict[type][0]
                    self.getMemberPropertiesPath()[attr]["maximum"] = defaultMinMaxDict[type][1]

class LeafTemplate(object):
    '''
    Class containeer which will serve as a template for model class key attrbibutes
    which must be entered by a user
    '''
    def __init__(self,):

        self.templateinfo = {
                "type" : "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description" : "what to display on the prompt when the user has entered a command",
                        "default": "",
                        "displayValue": False
                    },
                    "cliname": {
                        "type": "string",
                        "description": "name used in cli to describe bfd",
                        "default": ""
                    },
                    "help" : {
                        "type": "string",
                        "default": ""
                    },
                    "value": {
                        "type" : "object",
                        "description": "this is a trigger to cli that a command needs one of the attribute values contained "
                                        "in the properties commands LeafMemberTemplate",
                        "properties": {
                        }
                    },
                    "commands" : {
                        "type": "object",
                        "properties": {
                            "$ref": "",
                        }
                    },
                },
                "required" : list(["value", "cliname"]),
                "createwithdefault": {
                    "default": True,
                    "type": "boolean",
                    "description": "Attribute used to tell the cli whether an object can be created withdefaultref "
                                   "and/or default settings.  If this is false, all attributes must be set by user "
                                   "in order for create to be called."
                }
            }

    def getInfo(self):
        return self.templateinfo

    def getMemberPropertiesPath(self):

        return self.templateinfo["properties"]["value"]["properties"]

    def getCommandPath(self):

        return self.templateinfo["properties"]["commands"]["properties"]

    def setDefault(self, attr, v):
        if attr in self.getMemberPropertiesPath():
            self.getMemberPropertiesPath()[attr]["default"] = v

    def setArgType(self, type, selections=None, min=None, max=None):

        def isnumeric(type):
            return type in defaultMinMaxDict.keys()

        defaultMinMaxDict = {
            'int8': (-128, 127),
            'int16': (32768, 32767),
            'int32': (-2147483648, 2147483647),
            'int64': (-9223372036854775808, 9223372036854775807),
            'uint8': (0, 255),
            'uint16': (0, pow(2,16)),
            'uint32': (0, pow(2,32)),
            'uint64': (0, pow(2,64)),
        }
        if 'argtype' in self.getMemberPropertiesPath():
            self.getMemberPropertiesPath()['argtype']["type"] = type
            if selections and ("SELECTION" or "selections" in selections):
                # selections should be separated by /
                s = [x.lstrip(' ').rstrip(' ') for x in selections.split('/')]
                if len(s) and 'MIN' not in s[0]:
                    if isnumeric(type):
                        if '(' in s[0]:
                            s = [int(x.split('(')[1].rstrip(')')) for x in s if len(x.split('(')) > 1]
                        else:
                            import ipdb; ipdb.settrace()
                            s = [int(x) for x in s]
                    self.getMemberPropertiesPath()['argtype']["enum"] = s

            if isnumeric(type):
                if min is not None and max is not None:
                    self.getMemberPropertiesPath()['argtype']["minimum"] = min
                    self.getMemberPropertiesPath()['argtype']["maximum"] = max
                else:
                    self.getMemberPropertiesPath()['argtype']["minimum"] = defaultMinMaxDict[type][0]
                    self.getMemberPropertiesPath()['argtype']["maximum"] = defaultMinMaxDict[type][1]

    def setHelp(self, d, type=None, selections=None, min=None, max=None, len=None, default=None):
        lines = []
        if 'int' in type:
            if min not in ('', None) and max not in ('', None):
                lines.append("%s-%s  %s" %(min, max, d))
            elif selections not in ('', None):
                lines.append("%s  %s" %(selections, d))
            elif len not in ('', None):
                lines.append("len(%s) %s" %(len, d))
            else:
                lines.append("%s" %(d))
        elif type == 'bool':
            lines.append("True/False  %s" %(d, ))
        elif type == 'string':
            if selections not in ('', None):
                lines.append("%s  %s" %(selections, d))
            else:
                lines.append("%s" %(d, ))
        else:
            lines.append("type: %s.  %s" %(type, d))

        if default:
            lines.append("default: %s" %(default,))

        self.getMemberPropertiesPath()["help"]["default"] = " ".join(lines)

    def setSubCommandRef(self, filename):
        '''
        This will hold the dynamic subcommand reference that users will need to update to mach
        the model.
        :param filename:
        :return:
        '''

        self.getCommandPath().update({
            "$ref": GENERATED_SCHEMA_PATH + filename
        })

class ModelLeafMemberTemplate(ModelLeafTemplate):
    '''
    Class container to serve as a template to hold the attribute members of the model class
    '''
    def __init__(self):
        # the required fields
        self.templateinfo = {
                # what gets displayed when a tab is pressed
                "cliname": ""
            }

    def getMemberPropertiesPath(self):

        return self.templateinfo


class LeafMemberTemplate(LeafTemplate):
    '''
    Class container to serve as a template to hold the attribute members of the model class
    '''
    def __init__(self):
        self.templateinfo = {
                "type": "object",
                "properties" : {
                    # what gets saved to the prompt if set
                    # empty string means ignore
                    "prompt": {
                        "type": "string",
                        "default": ""
                    },
                    # what gets displayed when a tab is pressed
                    "cliname": {
                        "type": "string",
                        "default": ""
                    },
                    # description of what attribute value, ranges, default etc should be
                    # when user types ? or help
                    "help": {
                        "type": "string",
                        "default": "TODO"
                    },
                    # describes the type of the value that needs to be supplied
                    # if arg type will contain an enum if SELECTION is set in the model
                    "argtype": {
                        "type": "string"
                    },
                    "isdefaultset": {
                        "type": "boolean",
                        "default": False
                    },
                    # if a default is set then this will contain a value
                    "defaultarg" : {
                        "default": ""
                    },
                    # is the attribute a list of type?
                    "islist" :{
                        "type": "boolean",
                        "default": False
                    },
                    # determine if this attribute is a key to this object
                    "key" : {
                        "type": "boolean",
                        "default": False
                    }
                }
            }

    def getMemberPropertiesPath(self):

        return self.templateinfo["properties"]

class ModelToLeaf(object):
    SCHEMA_TYPE = 1
    MODEL_TYPE = 2

    def __init__(self, modeltype, frompath, topath):
        # lets get the model name for use in the schema
        self.modelname = frompath.split('/')[-1].split('Members.json')[0]
        self.modelpath = frompath
        self.clidatapath = topath
        self.modeltype = modeltype
        self.model = None
        self.template = None
        self.setTemplate()
        self.setCliData()

    def open(self):
        with open(self.modelpath, 'r') as f:
            self.model = json.load(f)

    def save(self):
        '''
        create two files if they don't exist:
        1) <ModelName>.json - holds the base class command
                The template data will then be stored into file
        2) <ModelName>SubCmds.json - This wil hold the dynamic information for sub commands related to
                Model command.

        :return:
        '''
        for filename, data, overwrite in ((self.clidatapath.split('Members.json')[0] + '.json', self.clidata, True),
                                          (self.clidatapath.split('Members.json')[0] + 'SubCmds.json', self.clisubcmddata, True)):

            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            if overwrite or not os.path.exists(filename):
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

    def setTemplate(self):
        if self.modeltype == self.SCHEMA_TYPE:
            self.template = LeafTemplate()
        else:
            self.template = ModelLeafTemplate()

    def setCliData(self):
        self.clidata = {self.modelname.lower(): {} }
        self.clisubcmddata = {}

    def setHelp(self):
        pass

    def build(self):
        self.open()
        self.setTemplate()
        self.setModelName()
        self.setCommands()

        # lets store off the data now
        self.clidata[self.modelname.lower()].update(self.template.getInfo())

    def setModelName(self):
        if self.modeltype == self.SCHEMA_TYPE:
            self.template.templateinfo['properties'].update({
                "objname": {
                "type": "string",
                "description": "object name to which references these attributes",
                "default": "%s" %(self.modelname)
                }
            })

    def setCommands(self):

        for name, member in self.model.iteritems():

            iskey = member['isKey']
            if iskey:
                type = member['type']
                isArray = member['isArray']
                description = member['description']
                default = member['default']
                isdefaultset = member['isDefaultSet'] if 'State' not in self.modelname else True
                #position = member['position']
                selections = member['selections'] if member['selections'] else None
                min = member['min'] if member['max'] else None
                max = member['max'] if member['max'] else None
                len = member['len'] if member['len'] else None

                memberinfo = LeafMemberTemplate() if self.modeltype == self.SCHEMA_TYPE else ModelLeafMemberTemplate()
                memberinfo.setDefault("cliname", name.lower())
                memberinfo.setDefault("key", iskey)
                memberinfo.setArgType(type, selections, min, max)
                memberinfo.setDefault("islist", isArray)
                memberinfo.setDefault("prompt", "")
                memberinfo.setDefault("defaultarg", default)
                memberinfo.setDefault("isdefaultset", isdefaultset)
                memberinfo.setHelp(description, type, selections, min, max, len, default if isdefaultset else None)
                #store the keys into the value attribute
                self.setLeafMembersRef(self.modelname+'Members.json', 1)
                self.template.setSubCommandRef(self.modelname+'SubCmds.json')
                if self.modeltype == self.SCHEMA_TYPE:
                    self.template.templateinfo['properties']['value']["properties"].update({name: memberinfo.getInfo()})
                else:
                    self.template.templateinfo['value'].update({name: memberinfo.getInfo()})

    def setLeafMembersRef(self, filename, idx):
        if self.modeltype == self.SCHEMA_TYPE:
            self.clisubcmddata.update({
                "subcmd%s" %(idx) : {
                    "$ref": GENERATED_SCHEMA_PATH + filename
                }
            })
        else:
            self.clisubcmddata.update({
                "subcmd%s" %(idx) : {
                    "$ref": GENERATED_MODEL_PATH + filename
                }
            })

# this class will take the generated json data model member files
# and create a schema from them
class ModelToLeafMember(ModelToLeaf):

    def save(self):
        if not os.path.exists(os.path.dirname(self.clidatapath)):
            try:
                os.makedirs(os.path.dirname(self.clidatapath))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(self.clidatapath, 'w') as f:
            json.dump(self.clidata, f, indent=2)

    def build(self):
        self.open()
        self.setModelName()
        self.setDefaultRef()
        self.setCommands()

    def setTemplate(self):
        if self.modeltype == self.SCHEMA_TYPE:
            self.template = {
                "commands": {
                    "type": "object",
                    "description": "",
                    "properties": {
                    },
                },
                "listattrs":[]
            }
        else:
            self.template = {"commands": {},
                             "listattrs": []}

    def setCliData(self):
        self.clidata = {}
        self.clisubcmddata = {}

    def setDefaultRef(self):
        '''
            The properties should can contain a reference of commands or the values themselves
            thus argument should be "subcmd" or "commands"  This should be set
            by the model, and can't be auto-generated as part of the schema.

            The cli engine will use this and the defaults on the object to determine
            if an object can be created initially.

        :return:
        '''
        if self.modeltype == self.SCHEMA_TYPE:
            self.clidata.update({
                "defaultref": {
                "type": "object",
                "properties": {},
                "description": "Object which contains defaults for the given object, the common case will "
                               "be a global object.  Flexswitch Model may have defaults set in model "
                               "they will be overwriten by what is defined here. If default is not "
                               "set in model or defaultref, then a 0 (int), true (bool) and '' (string) "
                               "will be used. This attribute will also be used on a deletion of an "
                               "attribute within an object.  A 'no attribute' will set the attribute "
                               "back to default"
                }
            })

    def setCreateWithDefaults(self, default):
        if self.modeltype == self.SCHEMA_TYPE:
            self.clidata.update({
                "createwithdefault": {
                "type" : "boolean",
                "description": "Attribute used to tell the cli whether an object can be created with"
                               "defaultref and/or default settings.  If this is false, all attributes "
                               "must be set by user in order for create to be called.",
                "default": default
                }
            })

    def setModelName(self):
        if self.modeltype == self.SCHEMA_TYPE:
            self.clidata.update({
                "objname": {
                "type": "string",
                "description": "object name to which references these attributes",
                "default": "%s" %(self.modelname)
                }
            })

    def setCommands(self):

        default = not False in [member['isDefaultSet'] for member in self.model.values() if not member['isKey']]
        self.setCreateWithDefaults(default)
        subcmdIdx = 1
        for name, member in self.model.iteritems():
            type = member['type']
            iskey = member['isKey']
            isArray = member['isArray']
            description = member['description']
            default = member['default']
            isdefaultset = member['isDefaultSet'] if 'State' not in self.modelname else True
            #position = member['position']
            selections = member['selections']
            min = member['min'] if member['max'] else None
            max = member['max'] if member['max'] else None
            len = member['len'] if member['len'] else None
            # state objects only require the keys for argument purposes
            if 'State' not in self.modelname or \
                iskey and 'State' in self.modelname:

                memberinfo = LeafMemberTemplate() if self.modeltype == self.SCHEMA_TYPE else ModelLeafMemberTemplate()
                if isCommonType(type):
                    memberinfo.setDefault("cliname", name.lower())
                    memberinfo.setDefault("key", iskey)
                    memberinfo.setArgType(type, selections, min, max)
                    memberinfo.setDefault("islist", isArray)
                    memberinfo.setDefault("prompt", "")
                    memberinfo.setDefault("defaultarg", default)

                    memberinfo.setHelp(description, type, selections, min, max, len, default if isdefaultset else None)
                    if self.modeltype == self.SCHEMA_TYPE:
                        self.template["commands"]["properties"].update({name: memberinfo.getInfo()})
                    else:
                        self.template["commands"].update({name: memberinfo.getInfo()})
                else: # complex key
                    memberinfo = LeafMemberTemplate() if self.modeltype == self.SCHEMA_TYPE else ModelLeafMemberTemplate()
                    subcmd = "subcmd%s" % subcmdIdx
                    if self.modeltype == self.SCHEMA_TYPE:
                        self.template["commands"]["properties"].update({subcmd:
                                                                    {"$ref": GENERATED_SCHEMA_PATH + type + '.json'}})
                    else:
                        self.template["commands"].update({subcmd:
                                                    {"$ref": GENERATED_MODEL_PATH + type + '.json'}})
                    # store mapping of attr to actually model attribute
                    self.template['listattrs'].append([subcmd, name])
                    subcmdIdx += 1

        self.clidata.update(self.template)


class ModelToCliSchemaBuilder(object):
    def __init__(self, cli_schema_path, cli_model_path, model_member_path):
        # path where data is going to go
        self.schemapath = cli_schema_path
        self.modelpath = cli_model_path
        # path where data is coming from
        self.codegenmodelpath = model_member_path


    def build(self, fileList=None):
        for root, dirs, filenames in os.walk(self.codegenmodelpath):
            for f in filenames:
                if 'Members' in f and \
                        (not fileList or f in fileList):
                    print(f)
                    for (obj, type, frompath, topath) in (
                        (ModelToLeaf, ModelToLeaf.SCHEMA_TYPE, self.codegenmodelpath + f, self.schemapath + f),
                        (ModelToLeafMember, ModelToLeaf.SCHEMA_TYPE, self.codegenmodelpath + f, self.schemapath + f),
                        (ModelToLeaf, ModelToLeaf.MODEL_TYPE, self.codegenmodelpath + f, self.modelpath + f),
                        (ModelToLeafMember, ModelToLeaf.MODEL_TYPE, self.codegenmodelpath + f, self.modelpath + f)):

                        data = obj(type, frompath, topath)
                        data.build()
                        data.save()

# *** MAIN LOOP ***
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-s", "--schema", action="store",type="string",
                      dest="cli_schema_path",
                      help="Path to the cli model to be used",
                      default="../schema/gen/")
    parser.add_option("-m", "--model", action="store",type="string",
                      dest="cli_model_path",
                      help="Path to the cli model to be used",
                      default="../models/cisco/gen/")
    parser.add_option("-d", "--datamodel", action="store", type="string",
                      dest="data_member_model_path",
                      help="Path to json data model member files",
                      default='../../../../../reltools/codegentools/._genInfo/')
    parser.add_option("-f", "--file", action="store", type="string",
                      dest="model_object_file_list",
                      help="List of files which to run codegen against seperated by ',' ",
                      default=None)

    (options, args) = parser.parse_args()

    # build the member data schema files
    x = ModelToCliSchemaBuilder(options.cli_schema_path,
                                options.cli_model_path,
                                options.data_member_model_path)
    fileList = options.model_object_file_list.split(',') if options.model_object_file_list is not None else []
    x.build(fileList)
