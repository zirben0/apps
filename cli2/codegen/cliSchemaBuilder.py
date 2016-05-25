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
import os, copy
from optparse import OptionParser


GENERATED_SCHEMA_PATH = '/tmp/snaproute/cli/schema/'

class ModelLeafTemplate(object):
    '''
    Class containeer which will serve as a template for model class key attrbibutes
    which must be entered by a user
    '''
    leafinfotemplate = {
        "prompt": "", # empty string will not display anything
        "cliname": "",
        "commands": {
            "description": "Commands must be in the format of 'subcmd<x>' which should contain"
                            "a $ref keyword or the command an be just Attribute : Value"
        },
        "createwithdefault": {
            "default": True,
            "type": "boolean",
            "description": "Attribute used to tell the cli whether an object can be created withdefaultref "
                           "and/or default settings.  If this is false, all attributes must be set by user "
                           "in order for create to be called."
        }
    }
    def __init__(self, frompath, topath):
        # lets get the model name for use in the schema
        self.modelname = frompath.split('/')[-1].split('Members.json')[0]
        self.modelpath = frompath
        self.schemapath = topath
        self.leafmodel = {}

    def setAdditionalShowCommands(self):
        self.leafmodel['commands'].update({
            "brief" : {
                "cliname": "brief",
            },
        })



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
                        "description": "holds all related sub command attributes related to this Leaf",
                        "properties": {
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

    def setPrompt(self, p):
        self.getMemberPropertiesPath()["prompt"]["default"] = p

    def setCliName(self, n):
        self.getMemberPropertiesPath()["cliname"]["default"] = n

    def setKey(self, k=False):
        self.getMemberPropertiesPath()["key"]["default"] = k

    def setDefault(self, d=""):
        self.getMemberPropertiesPath()["defaultarg"]["default"] = d

    def setType(self, t=str):
        self.getMemberPropertiesPath()["argtype"]["default"] = t

    def setIsList(self, l=False):
        self.getMemberPropertiesPath()["islist"]["default"] = l

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

    def setLeafMembersRef(self, filename, idx):

        self.getCommandPath().update({
            "subcmd%s" %(idx) : {
                "$ref": GENERATED_SCHEMA_PATH + filename
            }
        })

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
                    "argtype": {
                        "type": "string",
                        "default": ""
                    },
                    # if a default is set then this will contain a value
                    "defaultarg" : {
                        "type": "string",
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


class ModelToLeafSchema(object):
    def __init__(self, frompath, topath):
        # lets get the model name for use in the schema
        self.modelname = frompath.split('/')[-1].split('Members.json')[0]
        self.modelpath = frompath
        self.clidatapath = topath
        self.model = None
        self.template = None
        self.setTemplate()
        self.setCliData()

    def open(self):
        with open(self.modelpath, 'r') as f:
            self.model = json.load(f)

    def save(self):
        with open(self.clidatapath.split('Members.json')[0] + '.json', 'w') as f:
            json.dump(self.clidata, f, indent=2)

    def setTemplate(self):
        self.template = LeafTemplate()

    def setCliData(self):
        self.clidata = {self.modelname.lower(): {} }

    def build(self):
        self.open()
        self.setTemplate()
        self.setModelName()
        self.setCommands()

        # lets store off the data now
        self.clidata.update(
            {self.modelname.lower(): self.template.getInfo()}
        )


    def setModelName(self):
        self.clidata[self.modelname.lower()].update({
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
                iskey = member['isKey']
                isArray = member['isArray']
                description = member['description']
                default = member['default']
                isdefaultset = member['isDefaultSet']
                #position = member['position']
                selections = member['selections']
                min = member['min'] if member['max'] else None
                max = member['max'] if member['max'] else None
                len = member['len'] if member['len'] else None

                memberdata = LeafMemberTemplate()
                memberdata.setCliName(name.lower())
                memberdata.setKey(iskey)
                memberdata.setType(type)
                memberdata.setIsList(isArray)
                memberdata.setPrompt("")
                memberdata.setDefault(default)
                memberdata.setHelp(description, type, selections, min, max, len, default if isdefaultset else None)
                self.template.setLeafMembersRef(self.modelname+'Members.json', 1)

                #store the keys into the value attribute
                self.template.getMemberPropertiesPath().update(
                    {name: memberdata.getInfo()})


# this class will take the generated json data model member files
# and create a schema from them
class ModelToLeafMemberSchema(ModelToLeafSchema):

    def save(self):
        with open(self.clidatapath, 'w') as f:
            json.dump(self.clidata, f, indent=2)

    def build(self):
        self.open()
        self.setModelName()
        self.setCreateWithDefaults()
        self.setDefaultRef()
        self.setCommands()

    def setTemplate(self):
        self.template = {
            "commands": {
                "type": "object",
                "description": "",
                "properties": {
                }
            }
        }

    def setCliData(self):
        self.clidata = {}

    def setDefaultRef(self):
        '''
            The properties should can contain a reference of commands or the values themselves
            thus argument should be "subcmd" or "commands"  This should be set
            by the model, and can't be auto-generated as part of the schema.

            The cli engine will use this and the defaults on the object to determine
            if an object can be created initially.

        :return:
        '''
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

    def setCreateWithDefaults(self,):
        self.clidata.update({
            "createwithdefault": {
            "type" : "boolean",
            "description": "Attribute used to tell the cli whether an object can be created with"
                           "defaultref and/or default settings.  If this is false, all attributes "
                           "must be set by user in order for create to be called.",
            "default": False
            }
        })

    def setModelName(self):
        self.clidata.update({
            "objname": {
            "type": "string",
            "description": "object name to which references these attributes",
            "default": "%s" %(self.modelname)
            }
        })

    def setCommands(self):

        for name, member in self.model.iteritems():
            type = member['type']
            iskey = member['isKey']
            isArray = member['isArray']
            description = member['description']
            default = member['default']
            isdefaultset = member['isDefaultSet']
            #position = member['position']
            selections = member['selections']
            min = member['min'] if member['max'] else None
            max = member['max'] if member['max'] else None
            len = member['len'] if member['len'] else None
            # state objects only require the keys for argument purposes
            if 'State' not in self.modelname or \
                iskey and 'State' in self.modelname:

                memberinfo = LeafMemberTemplate()
                memberinfo.setCliName(name.lower())
                memberinfo.setKey(iskey)
                memberinfo.setType(type)
                memberinfo.setIsList(isArray)
                memberinfo.setPrompt("")
                memberinfo.setDefault(default)

                memberinfo.setHelp(description, type, selections, min, max, len, default if isdefaultset else None)
                self.template["commands"]["properties"].update({name: memberinfo.getInfo()})

        self.clidata.update(self.template)




class ModelToCliSchemaBuilder(object):
    def __init__(self, cli_schema_path, cli_model_path, model_member_path):
        # path where data is going to go
        self.schemapath = cli_schema_path
        self.modelpath = cli_model_path
        # path where data is coming from
        self.codegenmodelpath = model_member_path


    def build(self):
        for root, dirs, filenames in os.walk(self.codegenmodelpath):
            for f in filenames:
                if 'Members' in f:
                    print(f)

                    for (obj, frompath, topath) in (
                        (ModelToLeafSchema, self.codegenmodelpath + f, self.schemapath + f),
                        (ModelToLeafMemberSchema, self.codegenmodelpath + f, self.schemapath + f)):
                        #(ModelToLeafModel, self.codegenmodelpath + f, self.modelpath)):

                        data = obj(frompath, topath)
                        data.build()
                        data.save()

# *** MAIN LOOP ***
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-s", "--schema", action="store",type="string",
                      dest="cli_schema_path",
                      help="Path to the cli model to be used",
                      default="../schema/")
    parser.add_option("-m", "--model", action="store",type="string",
                      dest="cli_model_path",
                      help="Path to the cli model to be used",
                      default="../models/cisco/")
    parser.add_option("-d", "--datamodel", action="store", type="string",
                      dest="data_member_model_path",
                      help="Path to json data model member files",
                      default='../../../../../reltools/codegentools/._genInfo/')

    (options, args) = parser.parse_args()

    # build the member data schema files
    x = ModelToCliSchemaBuilder(options.cli_schema_path,
                                options.cli_model_path,
                                options.data_member_model_path)
    x.build()
