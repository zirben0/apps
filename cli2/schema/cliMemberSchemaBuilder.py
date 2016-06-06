#!/usr/bin/python

import json
import os, copy
from optparse import OptionParser

class MemberTemplate(object):
    info = {
            "type" : 'object',
            "properties": {
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

    def getInfo(self):
        return self.info

    def setPrompt(self, p):
        self.info["properties"]["prompt"]["default"] = p

    def setCliName(self, n):
        self.info["properties"]["cliname"]["default"] = n

    def setKey(self, k=False):
        self.info["properties"]["key"]["default"] = k

    def setDefault(self, d=""):
        self.info["properties"]["defaultarg"]["default"] = d

    def setType(self, t=str):
        self.info["properties"]["argtype"]["default"] = t

    def setIsList(self, l=False):
        self.info["properties"]["islist"]["default"] = l

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

        self.info["properties"]["help"]["default"] = " ".join(lines)

# this class will take the generated json data model member files
# and create a schema from them
class ModelMemberSchemaFormat(object):
    def __init__(self, frompath, topath):
        # lets get the model name for use in the schema
        self.modelname = frompath.split('/')[-1].split('Members.json')[0]
        self.modelpath = frompath
        self.schemapath = topath
        self.memberschema = {}
        self.membermodel = None

    def open(self):
        with open(self.modelpath, 'r') as f:
            self.membermodel = json.load(f)

    def build(self):
        self.open()
        self.setModelName()
        self.setCommands()

    def save(self):
        with open(self.schemapath, 'w+') as f:
            json.dump(self.memberschema, f, indent=2)

    def setModelName(self):
        self.memberschema["objname"] = {
            "type": "string",
            "descirption": "object name to which references these attributes",
            "default": "%s" %(self.modelname)
        }
    def setCommands(self):

        self.memberschema["commands"] = {
            "type": "object",
            "description": "",
            "properties": { } # where member info is stored
        }
        for name, member in self.membermodel.iteritems():
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

            memberinfo = MemberTemplate()
            memberinfo.setCliName(name.lower())
            memberinfo.setKey(iskey)
            memberinfo.setType(type)
            memberinfo.setIsList(isArray)
            memberinfo.setPrompt("")
            memberinfo.setDefault(default)

            memberinfo.setHelp(description, type, selections, min, max, len, default if isdefaultset else None)

            self.memberschema["commands"]["properties"].update(
                {name : copy.deepcopy(memberinfo.getInfo())})




class CliMemberSchemaBuilder(object):
    def __init__(self, cli_schema_path, model_member_path):
        self.schemapath = cli_schema_path
        self.codegenmodelpath = model_member_path

    def build(self):
        for root, dirs, filenames in os.walk(self.codegenmodelpath):
            for f in filenames:
                if 'Members' in f:
                    print(f)
                    objData = ModelMemberSchemaFormat(self.codegenmodelpath + f,
                                                      self.schemapath + f)
                    objData.build()
                    objData.save()


# *** MAIN LOOP ***
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-j", "--jschema", action="store",type="string",
                      dest="cli_schema_path",
                      help="Path to the cli model to be used",
                      default="./")
    parser.add_option("-d", "--jdatamodel", action="store", type="string",
                      dest="data_member_model_path",
                      help="Path to json data model member files",
                      default='../../../../../reltools/codegentools/._genInfo/')


    (options, args) = parser.parse_args()

    cli_schema_path = options.cli_schema_path
    data_member_model_path = options.data_member_model_path
    # build the member data schema files
    x = CliMemberSchemaBuilder(cli_schema_path, data_member_model_path)
    x.build()
