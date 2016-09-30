#!/usr/bin/python
#
# Copyright [2016] [SnapRoute Inc]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
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
#
# This file will build the CLI tree based on the Schema and Cisco Model
# As of 9/30/16 it expects that the json cli model file has already been created
import json
import os
import sys
import copy
from optparse import OptionParser


GENERATED_SCHEMA_PATH = 'file:/tmp/snaproute/cli/schema/'
GENERATED_MODEL_PATH = 'file:/tmp/snaproute/cli/model/cisco/'

EXAMPLE_LIST = ("example", )
EXIT_LIST = ("exit", )

STDIO_OUT_RED = '\033[31m'
STDIO_OUT_RED_END = '\033[00m'
STDIO_OUT_GREEN = '\033[32m'
STDIO_OUT_GREEN_END = '\033[00m'
STDIO_OUT_YELLOW = '\033[93m'
STDIO_OUT_YELLOW_END = '\033[00m'
STDIO_OUT_BOLD = '\033[1m'
STDIO_OUT_BOLD_END = '\033[00m'


def print_yellow(lines):
    sys.stdout.write(STDIO_OUT_YELLOW + lines + STDIO_OUT_YELLOW_END)


def print_red(lines):
    sys.stdout.write(STDIO_OUT_RED + lines + STDIO_OUT_RED_END)


def print_green(lines):
    sys.stdout.write(STDIO_OUT_GREEN + lines + STDIO_OUT_GREEN_END)


def print_default(lines):
    sys.stdout.write(lines)


def print_example(filenames):

    print_default("Example file names: ")
    for name in filenames:
        print_default(STDIO_OUT_BOLD + name + STDIO_OUT_BOLD_END)
    print_default("\n")


def get_cmd():
    cmd = sys.stdin.readline().rstrip("\n")
    if cmd.lower in EXIT_LIST:
        print_yellow("Exiting....")
        sys.exit(0)
    return cmd


class CliCmdTreeHelper(object):

    # three different model file types
    MODEL_TYPE_KEY = "Key"
    MODEL_TYPE_ATTRS = "Attributes"
    MODEL_TYPE_SUBCMDS = "SubCmds"
    MODEL_TYPE_UNKNOWN = "Unknown"

    """
    This class is meant to make it easier to add a command to the cli model
    """
    def __init__(self, schema_path, model_path):
        # location of the model files
        self.schema_path = schema_path
        self.model_path = model_path

        self.src_file = None
        self.save_file = None
        self.insertion_file = None
        self.src_model_data = None
        self.src_schema_data = None

        self.cmd_type = "config"
        self.model_type = self.MODEL_TYPE_UNKNOWN

    def run_create(self,):
        # TODO, for now users can run cliSchemaBuilder which will automatically build a model based on the model json
        pass

    def run_update(self,):
        """
        This is to be run if the model object already exists and we want to just update the contents
        and add it to the model
        :return:
        """
        self.get_cmd_type()
        self.get_model_type()
        self.get_model_file_name()
        self.get_saved_file_name()
        if self.model_type == self.MODEL_TYPE_KEY:
            self.get_cli_location_to_insert_model()
        self.update_cmd_object()
        self.insert_new_commands_to_model()

    @staticmethod
    def check_if_valid_model_exists(path_filename):
        return os.path.exists(os.path.dirname(path_filename))

    @staticmethod
    def update_attribute_info(key, clinamedict, update_data, baseobjdict=None):

        print_default("Do you wish to include attr %s for this object [y]/n:" % (key, ))
        include_attribute = get_cmd()
        if include_attribute.lower() in ("y", ""):
            print_default("What cli name do you want to display for this attr %s [%s]" % (key, clinamedict["cliname"]))
            cli_name = get_cmd()

            if cli_name:
                update_data.update({key: {"cliname": cli_name}})
            else:
                update_data.update({key: clinamedict})

            # used for object key json
            if baseobjdict and baseobjdict.get('cliname') == "":
                print_default("Is this the base key attr to display [y]/n:")
                base_attribute = get_cmd()
                if base_attribute.lower() in ("y", ""):
                    baseobjdict['cliname'] = cli_name

    def get_model_type(self):

        while True:
            print_default("What type of model file is being added [Keys]/Members:")
            model_type = get_cmd()
            if model_type in ("Keys", ""):
                self.model_type = self.MODEL_TYPE_KEY
                return
            elif model_type == "Members":
                self.model_type = self.MODEL_TYPE_ATTRS
                return
            else:
                print_red("Unknown selection must be [Keys,Members]")

    def get_cmd_type(self):
        while True:
            print_default("What type of command is this [config]/show:")
            cmd_type = get_cmd()
            if cmd_type.lower() in ("config", "show", ""):
                self.cmd_type = cmd_type.lower() if cmd_type else "config"
                return
            elif cmd_type.lower in EXIT_LIST:
                sys.exit(0)

    def get_model_file_name(self):
        while True:
            print_default("Enter Model filename you wish to add to cli:")
            filename = get_cmd()
            if filename in ("", ):
                continue
            elif filename in EXAMPLE_LIST:
                print_example(["NEWMODLEOBJECT.json", "EXAMPLE.json", "myexample.json"])
            elif self.check_if_valid_model_exists(self.schema_path + filename) and \
                    self.check_if_valid_model_exists(self.model_path + filename):
                self.src_file = filename
                # TODO should do some error checking to ensure that model file is the
                # same as the model_type
                with open(self.schema_path + self.src_file, 'r+') as f1:
                    self.src_schema_data = json.load(f1)

                with open(self.model_path + self.src_file, 'r+') as f2:
                    self.src_model_data = json.load(f2)
                return
            else:
                print_red("ERROR: file does not exist %s" % (filename, ))

    def get_saved_file_name(self):
        print_default("Enter name of file to be saved after edits [%s]:" % (self.src_file, ))
        filename = get_cmd()
        self.save_file = filename
        if filename in ("", ):
            self.save_file = self.src_file

    def get_cli_location_to_insert_model(self,):
        while True:
            print_default("Enter file tree location you wish to insert into cli tree: [ignore]")
            filename = get_cmd()
            if filename in ("ignore", ""):
                return
            elif filename.lower() in EXAMPLE_LIST:
                print_example(['base.json', 'interface.json', "show.json"])
            elif filename.lower() in EXIT_LIST or \
                    self.check_if_valid_model_exists(self.schema_path + filename) and \
                    self.check_if_valid_model_exists(self.model_path + filename):
                self.insertion_file = filename
                return
            else:
                print_red("ERROR: file does not exist %s" % (filename, ))

    def update_cmd_key_object(self,):
        default_help = ""
        objname = ""
        schemadata = self.src_schema_data
        for attr in schemadata.values():
            objname = attr["properties"]["objname"]["default"]
            if self.cmd_type == "config":
                default_help = "Configuring %s attributes" % (objname, )
            elif self.cmd_type == "show":
                default_help = "Show All %s Objects" % (objname, )

        data = self.src_model_data
        for key, datadict in copy.deepcopy(data).iteritems():

            data[key]["help"] = default_help
            print_default("What should be display on the prompt after the command is entered [""]:")
            data[key]['prompt'] = get_cmd()

            print_default("Enter Object Help Command [default]")
            objhelp = get_cmd()
            if objhelp:
                data[key]['help'] = objhelp

            print_yellow("\nNow to Set the cli display name for the keys for %s\n" % (objname, ))
            print_yellow("This command name will be shown in the cli menu and should be\n")
            print_yellow("tied to a key attribute for this model.  For example:\n")
            print_yellow("Acl.json has keys [Aclname, Direction], if I changed the name\n")
            print_yellow("of Aclname to just name that is how it would display in the \n")
            print_yellow("help and tab completion, however this does not really describe what this\n")
            print_yellow("object is configuring, so a better choice would be 'acl'\n\n")

            for attr, clinamedict in datadict['value'].iteritems():
                self.update_attribute_info(attr,
                                           clinamedict,
                                           data[key]['value'],
                                           baseobjdict=data[key])
        # save the data
        with open(self.model_path + self.save_file, 'w') as f3:
            # save the info
            json.dump(data, f3, indent=2)

    def update_cmd_members_object(self):

        with open(self.model_path + self.src_file, 'r+') as f2:
            data = json.load(f2)
            for key, datadict in copy.deepcopy(data).iteritems():
                if key == "commands":
                    for attr, clinamedict in datadict.iteritems():
                        self.update_attribute_info(attr,
                                                   clinamedict,
                                                   data[key],
                                                   baseobjdict=data[key])

            with open(self.model_path + self.save_file, 'w') as f3:
                # save the info
                json.dump(data, f3, indent=2)

    def update_cmd_object(self):

        # depending on the file x.json, xMembers.json, xSubCmds.json will
        # require different actions

        if self.model_type == self.MODEL_TYPE_ATTRS:
            self.update_cmd_members_object()
        elif self.model_type == self.MODEL_TYPE_KEY:
            self.update_cmd_key_object()

    def insert_new_commands_to_model(self):
        if self.insertion_file:
            with open(self.schema_path + self.insertion_file, 'r+') as f1:
                schemadata = json.load(f1)

                subcmds = schemadata[self.cmd_type]["properties"]["commands"]["properties"].keys()
                keynums = [int(subcmd.lstrip("subcmd")) for subcmd in subcmds]
                num = list(frozenset([x for x in range(1, len(keynums))]).difference(keynums))
                new_subcmd_key = "subcmd" + str(len(keynums) + 1)
                if num:
                    new_subcmd_key = "subcmd" + str(num[0])

                schemadata[self.cmd_type]["properties"]["commands"]["properties"].update(
                    {new_subcmd_key: GENERATED_SCHEMA_PATH + self.save_file}
                )

                with open(self.schema_path + self.insertion_file, 'w') as f2:
                    # save the info
                    json.dump(schemadata, f2, indent=2)

            with open(self.model_path + self.insertion_file, 'r+') as f3:
                modeldata = json.load(f3)

                modeldata[self.cmd_type]["commands"].update(
                    {new_subcmd_key: {"$ref": GENERATED_MODEL_PATH + self.save_file}}
                )

                with open(self.model_path + self.insertion_file, 'w') as f4:
                    # save the info
                    json.dump(modeldata, f4, indent=2)


def show_cli_intro():
        print_yellow("Hello I am here to help you add a command to the CLI\n")
        print_yellow("At any point during the step by step process if you wish\n")
        print_yellow("to quit you can type exit or Ctr-Z.\n")
        print_yellow("You can also type example if you are not sure what to add.\n\n")


def display_menu():
    print_default("Enter what CLI action you would like to perform [update]\create\delete]:")
    s = sys.stdin.readline().rstrip("\n")
    if s.lower() in ("update", ""):
        return "update"
    elif s.lower() in ("create", ):
        return "created"
    elif s.lower() in ("delete", ):
        return "delete"


# *** MAIN LOOP ***
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-s", "--schema", action="store", type="string",
                      dest="cli_schema_path",
                      help="Path to the cli model to be used",
                      default="../schema/")
    parser.add_option("-m", "--model", action="store", type="string",
                      dest="cli_model_path",
                      help="Path to the cli model to be used",
                      default="../models/cisco/")

    (options, args) = parser.parse_args()

    show_cli_intro()
    sel = display_menu()

    model_helper = CliCmdTreeHelper(options.cli_schema_path,
                                    options.cli_model_path)

    if sel == "update":
        model_helper.run_update()
    elif sel == "create":
        model_helper.run_create()
    elif sel == "delete":
        # TOOD
        pass