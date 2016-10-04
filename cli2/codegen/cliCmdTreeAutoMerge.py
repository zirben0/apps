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
from jsondiff import diff


GENERATED_SCHEMA_PATH = 'file:/tmp/snaproute/cli/schema/'
GENERATED_MODEL_PATH = 'file:/tmp/snaproute/cli/model/cisco/'

EXCLUDE_OBJECT_PATH_FILE = "../excludeObj.json"

MERGE_HISTORY_FILE = 'mergeHistory.txt'

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


class CliCmdTreeAutoMerge(object):

    # three different model file types
    MODEL_TYPE_KEY = "Key"
    MODEL_TYPE_ATTRS = "Attributes"
    MODEL_TYPE_SUBCMDS = "SubCmds"
    MODEL_TYPE_UNKNOWN = "Unknown"

    """
    This class is meant to make it easier to add a command to the cli model
    """
    def __init__(self, schema_path, schema_gen_path, model_path, model_gen_path, flex_model_obj_jsons, single_json):
        # location of the model files
        self.schema_path = schema_path
        self.schema_gen_path = schema_gen_path
        self.model_path = model_path
        self.model_gen_path = model_gen_path

        # location of flexswitch model files in json format
        self.flexswitch_model_path = flex_model_obj_jsons
        self.single_file_merge = single_json
        self.exclude_data_list = []

        self.model_obj_to_file_list = {}
        self.gen_model_obj_to_file_list = {}
        self.schema_obj_to_file_list = {}
        self.gen_schema_obj_to_file_list = {}

    def run(self,):
        """
        This is to be run if the model object already exists and we want to just update the contents
        and add it to the model
        :return:
        """
        self.get_excludeobj_list()
        self.build_obj_to_file_list()
        self.build_new_obj_files_list()
        #self.merge_existing_model_file_changes()

    @staticmethod
    def find_model_objs_by_objname(schema_obj_path,
                                   model_obj_path,
                                   objname):
        """

        :param schema_obj_path:
        :param model_obj_path:
        :param objname:
        :return:
        """
        files_to_skip = ['base.json', 'config.json', 'show.json']

        schema_obj_to_file_list = {"Members": [],
                                   "Keys": []}
        model_obj_to_file_list = {"Members": [],
                                  "Keys": []}
        # we have the model object now lets find all the files who use this model object
        for root, dirs, genfilenames in os.walk(schema_obj_path):
            for f in genfilenames:
                if f.endswith(".json") and f not in files_to_skip:
                    if os.path.exists(schema_obj_path + f):
                        with open(schema_obj_path + f, 'r') as f2:
                            obj = json.load(f2)

                            key = "Members"
                            found_objname = None
                            # members file
                            if "commands" in obj:
                                if 'objname' in obj:
                                    found_objname = obj['objname']['default']
                            elif [key for key in obj.keys() if "subcmd" in key]:
                                continue
                            else:
                                # key object file
                                for d in obj.values():
                                    if 'objname' in d['properties']:
                                        found_objname = d['properties']['objname']['default']
                                        key = "Keys"
                                        break
                            if found_objname == objname:
                                schema_obj_to_file_list[key].append((f, obj))
                                if not os.path.exists(model_obj_path + f):
                                    print_red("ERROR file %s exists in schema but not in model" % (f,))

                                with open(model_obj_path + f, 'r') as f3:
                                    modelobj = json.load(f3)
                                    model_obj_to_file_list[key].append((f, modelobj))

        return schema_obj_to_file_list, model_obj_to_file_list

    def get_excludeobj_list(self):

        with open(EXCLUDE_OBJECT_PATH_FILE, "r") as f:
            self.exclude_data_list = json.load(f)["Exclude"]
            # convert these to json key file names
            self.exclude_data_list = [x + ".json" for x in self.exclude_data_list]

    def build_obj_to_file_list(self, ):
        """
        Build a list of all the files associated with a given object in both the
        generated dir and the actual directory containing the models
        :return:
        """
        # two cases 1 file or all files
        if not self.single_file_merge:
            for root, dirs, filenames in os.walk(self.flexswitch_model_path):
                for f in filenames:
                    if 'Members' in f:
                        objname = f.replace("Members.json", "")
                        self.gen_schema_obj_to_file_list.update({objname: {}})
                        self.schema_obj_to_file_list.update({objname: {}})
                        self.gen_model_obj_to_file_list.update({objname: {}})
                        self.model_obj_to_file_list.update({objname: {}})

                        self.gen_schema_obj_to_file_list[objname], self.gen_model_obj_to_file_list[objname] = \
                            self.find_model_objs_by_objname(self.schema_gen_path,
                                                            self.model_gen_path,
                                                            objname)

                        self.schema_obj_to_file_list[objname], self.model_obj_to_file_list[objname] = \
                            self.find_model_objs_by_objname(self.schema_path,
                                                            self.model_path,
                                                            objname)
                        import ipdb; ipdb.set_trace()

        else:
            # open single file
            pass

    def add_state_obj_to_cli_show_cmds(self, schemadata, modeldata, f):
        self.add_obj_to_cli_subcmd(schemadata, modeldata, f, "show")

    def add_config_obj_to_cli_config_cmds(self, schemadata, modeldata, f):
        self.add_obj_to_cli_subcmd(schemadata, modeldata, f, "config")

    @staticmethod
    def add_obj_to_cli_subcmd(schemadata, modeldata, f, cmd_type):

        def get_subcmd():
            # see if command exists, if it does not return
            # next valid command
            subcmds = []
            for cmd, refdict in schemadata[cmd_type]["properties"]["commands"]["properties"].iteritems():
                subcmds.append(cmd)
                for fileref in refdict.values():
                    if f == fileref.split("/")[-1]:
                        return cmd

            keynums = [int(cmd.lstrip("subcmd")) for cmd in subcmds]
            num = list(frozenset([x for x in range(1, len(keynums))]).difference(keynums))
            new_subcmd_key = "subcmd" + str(len(keynums) + 1)
            if num:
                new_subcmd_key = "subcmd" + str(num[0])
            return new_subcmd_key

        subcmd = get_subcmd()

        schemadata[cmd_type]["properties"]["commands"]["properties"].update(
            {subcmd: {"$ref": GENERATED_SCHEMA_PATH + f}}
        )
        print "schema inserting: ", {subcmd: GENERATED_SCHEMA_PATH + f}

        modeldata[cmd_type]["commands"].update(
            {subcmd: {"$ref": GENERATED_MODEL_PATH + f}}
        )
        print "model inserting: ", {subcmd: GENERATED_MODEL_PATH + f}

    def cp_gen_file_to_master_dir(self, f_list):
        # could just do a copy but this will also verify the
        # syntax of the json files

        for f in f_list:
            with open(self.schema_gen_path + f, 'r') as f1:
                schemadata = json.load(f1)

                print "copying file: ", self.schema_gen_path + f, "to:", self.schema_path + f
                with open(self.schema_path + f, 'w+') as f2:
                    # save the info
                    json.dump(schemadata, f2, indent=2)

                with open(self.model_gen_path + f, 'r') as f3:
                    modeldata = json.load(f3)

                    print "copying file: ", self.model_gen_path + f, "to:", self.model_path + f
                    with open(self.model_path + f, 'w+') as f4:
                        # save the info
                        json.dump(modeldata, f4, indent=2)

    def get_show_config_json_data(self):
        with open(self.schema_path + 'show.json', 'r+') as f1:
            showschemadata = json.load(f1)

        with open(self.model_path + 'show.json', 'r+') as f1:
            showmodeldata = json.load(f1)

        with open(self.schema_path + 'config.json', 'r+') as f1:
            configschemadata = json.load(f1)

        with open(self.model_path + 'config.json', 'r+') as f1:
            configmodeldata = json.load(f1)

        return showschemadata, showmodeldata, configschemadata, configmodeldata

    def save_show_config_json_data(self, showschemadata, showmodeldata, configschemadata, configmodeldata):
        with open(self.schema_path + 'show.json', 'w') as f2:
            # save the info
            json.dump(showschemadata, f2, indent=2)
        with open(self.model_path + 'show.json', 'w') as f2:
            # save the info
            json.dump(showmodeldata, f2, indent=2)
        with open(self.schema_path + 'config.json', 'w') as f2:
            # save the info
            json.dump(configschemadata, f2, indent=2)
        with open(self.model_path + 'config.json', 'w') as f2:
            # save the info
            json.dump(configmodeldata, f2, indent=2)

    def build_new_obj_files_list(self, ):
        """
        When adding a generated model command you only care about the Keys command
        as the subcmd and members is already linked the the keys
        :return:
        """
        new_schema_files = []
        new_model_files = []
        for objname, f_dict in self.gen_schema_obj_to_file_list.iteritems():
            # new_schema_files += list(frozenset(f_dict["Members"]).difference(self.schema_obj_to_file_list[objname]))
            gen_file_list = [f for (f, data) in f_dict["Keys"]]
            file_list = [f for (f, data) in self.schema_obj_to_file_list[objname]["Keys"]]
            new_schema_files += list(frozenset(gen_file_list).difference(file_list))
            # files_to_be_merged = frozenset(f_list).intersection(f_list)

        for objname, f_dict in self.gen_model_obj_to_file_list.iteritems():
            # new_model_files += list(frozenset(f_dict["Members"]).difference(self.model_obj_to_file_list[objname]))
            gen_file_list = [f for (f, data) in f_dict["Keys"]]
            file_list = [f for (f, data) in self.model_obj_to_file_list[objname]["Keys"]]
            new_schema_files += list(frozenset(gen_file_list).difference(file_list))
            # files_to_be_merged = frozenset(f_list).intersection(f_list)

        num_schema_files = len(new_schema_files)
        num_model_files = len(new_model_files)

        # get the json data files
        showschemadata, showmodeldata, configschemadata, configmodeldata = self.get_show_config_json_data()

        if num_model_files > 0 and \
            num_model_files == num_schema_files and \
                len(frozenset(new_schema_files).intersection(new_model_files)) == num_schema_files:
            print "new schema/model files: %s" % (num_schema_files, )

            for f in new_schema_files:
                self.cp_gen_file_to_master_dir([f,
                                                f.replace(".json", "") + "Members.json",
                                                f.replace(".json", "") + "SubCmds.json"])

                if f not in self.exclude_data_list:
                    if "State" in f:
                        self.add_state_obj_to_cli_show_cmds(showschemadata, showmodeldata, f)
                    else:
                        self.add_config_obj_to_cli_config_cmds(configschemadata, configmodeldata, f)
        else:
            print_red("ERROR mismatch in new model/schema files\nschema %s\nmodel %s\n" % (
                new_schema_files, new_model_files))

        # json data has been updated lets update it
        self.save_show_config_json_data(showschemadata, showmodeldata, configschemadata, configmodeldata)

    def compare_gen_to_master_data(self, gen_data, master_data):
        import ipdb; ipdb.set_trace()
        print diff(gen_data, master_data)


    def merge_existing_model_file_changes(self, ):
        existing_members_schema_files = []
        existing_keys_schema_files = []
        for objname, f_dict in self.gen_schema_obj_to_file_list.iteritems():
            gen_file_list = [f for (f, data) in f_dict["Keys"]]
            file_list = [f for (f, data) in self.schema_obj_to_file_list[objname]["Keys"]]
            mem_gen_file_list = [f for (f, data) in f_dict["Members"]]
            mem_file_list = [f for (f, data) in self.schema_obj_to_file_list[objname]["Members"]]

            print "schema:", objname, gen_file_list, file_list

            # these are the files which are the same we need to see if we need to merge them
            existing_members_schema_files += list(frozenset(mem_gen_file_list).intersection(mem_file_list))
            existing_keys_schema_files += list(frozenset(gen_file_list).intersection(file_list))

        # dict of file comparison
        compare_members_schema_files = {}
        for f in existing_members_schema_files:
            print "existing file:", f
            for objname, f_dict in self.gen_schema_obj_to_file_list.iteritems():
                for fname, fdata in f_dict["Keys"]:
                    if f == fname:
                        compare_members_schema_files.update({f: [fdata, ]})
                for fname, fdata in f_dict["Members"]:
                    if f == fname:
                        compare_members_schema_files.update({f: [fdata, ]})

            for objname, f_dict in self.schema_obj_to_file_list.iteritems():
                for fname, fdata in f_dict["Keys"]:
                    if f == fname:
                        compare_members_schema_files[f].append(fdata)
                for fname, fdata in f_dict["Members"]:
                    if f == fname:
                        compare_members_schema_files[f].append(fdata)

        '''
        existing_members_model_files = []
        existing_keys_model_files = []
        for objname, f_dict in self.gen_model_obj_to_file_list.iteritems():
            gen_file_list = [f for (f, data) in f_dict["Keys"]]
            file_list = [f for (f, data) in self.model_obj_to_file_list[objname]["Keys"]]
            mem_gen_file_list = [f for (f, data) in f_dict["Members"]]
            mem_file_list = [f for (f, data) in self.model_obj_to_file_list[objname]["Members"]]

            # these are the files which are the same we need to see if we need to merge them
            existing_members_model_files += list(frozenset(mem_gen_file_list).difference(mem_file_list))
            existing_keys_model_files += list(frozenset(gen_file_list).difference(file_list))
        '''
        import ipdb; ipdb.set_trace()
        for f, (d1, d2) in compare_members_schema_files.iteritems():
            print 'comparing schema file:', f
            self.compare_gen_to_master_data(d1, d2)


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
    parser.add_option("-d", "--datamodel", action="store", type="string",
                      dest="data_member_model_path",
                      help="Path to json data model member files",
                      default='../../../../../reltools/codegentools/._genInfo/')
    parser.add_option("-f", "--file", action="store", type="string",
                      dest="model_object_file_list",
                      help="List of files which to run codegen against seperated by ',' ",
                      default=None)

    (options, args) = parser.parse_args()

    model_helper = CliCmdTreeAutoMerge(options.cli_schema_path,
                                       options.cli_schema_path + "gen/",
                                       options.cli_model_path,
                                       options.cli_model_path + "gen/",
                                       options.data_member_model_path,
                                       options.model_object_file_list)
    model_helper.run()