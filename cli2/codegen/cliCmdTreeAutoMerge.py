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
import pprint
import copy
from optparse import OptionParser
from jsondiff import diff, update, delete, add, replace, insert, missing
from snapcliconst import DYNAMIC_MODEL_ATTR_NAME_LIST

pp = pprint.PrettyPrinter(indent=2)

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


class ModelMergeCommon(object):
    def __init__(self, path, f, data_diff, olddata, newdata):
        self.path = path
        self.model_file = f
        self.data_diff = data_diff
        self.olddata = olddata
        self.newdata = newdata

    def diff_tree_walk_generator(self, indict, pre=None):
        pre = pre[:] if pre else []
        if isinstance(indict, dict):
            for key, value in indict.items():
                if isinstance(value, dict) and len(value) != 0:
                    for d in self.diff_tree_walk_generator(value, [key] + pre):
                        yield d
                elif isinstance(value, list) or isinstance(value, tuple):
                    for v in value:
                        for d in self.diff_tree_walk_generator(v, [key] + pre):
                            yield d
                else:
                    rv = [value, key] + pre
                    rv.reverse()
                    yield rv
        else:
            rv = [indict] + pre
            rv.reverse()
            yield rv


class SchemaModelMembersMerge(ModelMergeCommon):

    def insert_model_command_attribute(self, attr_name, diff_walk_data_list):
        """
        Only insert if the schema does not indicate that the attribute has been changed
        :param attr_name:
        :param diff_walk_data_list:
        :return:
        """
        if "cmd_to_subcmd" in self.olddata:
            if attr_name in self.olddata["cmd_to_subcmd"].values():
                # nothing to do as this command was user entered
                return

        attr_dict = {
            attr_name: {
                "type": None,
                "properties": {}
                }
            }
        for diff_walk_data in diff_walk_data_list:
            try:
                properties_or_type = diff_walk_data[3]
                if len(diff_walk_data) == 10:
                    attr = diff_walk_data[7]
                    attr_properties_dict = {
                        attr: {diff_walk_data[8]: diff_walk_data[9]}
                    }
                else:
                    attr = diff_walk_data[6]
                    attr_properties_dict = {
                        attr: diff_walk_data[7]
                    }

                if properties_or_type == "type":
                    self.olddata["commands"][properties_or_type].update(attr_properties_dict)
                else:  # properties
                    if attr == "type":
                        attr_dict[attr_name].update(attr_properties_dict)
                    elif attr not in attr_dict[attr_name]["properties"]:
                        attr_dict[attr_name]["properties"].update(attr_properties_dict)
                    else:
                        attr_dict[attr_name]["properties"][attr].update(attr_properties_dict[attr])

                    self.olddata["commands"]["properties"].update(attr_dict)
            except Exception as e:
                print e, diff_walk_data

    def update_model_command_attribute(self, attr_name, diff_walk_data):
        #  fixed location format
        if "cmd_to_subcmd" in self.olddata:
            if attr_name in self.olddata["cmd_to_subcmd"].values():
                #  nothing to do as this command was user entered
                return
        try:
            cmd = diff_walk_data[1]
            cmd_prop = diff_walk_data[3]
            if diff_walk_data[4] == update:
                model_attr = diff_walk_data[5]
                model_prop = diff_walk_data[7]
                if model_prop == "properties":
                    model_prop_attr = diff_walk_data[9]
                    diff_cmd = diff_walk_data[10]
                    model_prop_attr_default = diff_walk_data[11]
                    if diff_cmd == update:
                        model_prop_attr_default_value = diff_walk_data[12]
                        self.olddata[cmd][cmd_prop][model_attr][model_prop][model_prop_attr][
                                model_prop_attr_default] = model_prop_attr_default_value
                    elif diff_cmd == delete:
                        # merge
                        try:
                            del self.olddata[cmd][cmd_prop][model_attr][model_prop][model_prop_attr][
                                model_prop_attr_default]
                        except KeyError:
                            pass
                    elif diff_cmd == insert:
                        import ipdb; ipdb.set_trace()
                else:  # type
                    self.olddata[cmd][cmd_prop][model_attr][model_prop] = diff_walk_data[8]
        except Exception as e:
            print e, diff_walk_data

    def delete_model_command_attribute(self, attr_name, diff_walk_data):
        if "cmd_to_subcmd" in self.olddata:
            if attr_name in self.olddata["cmd_to_subcmd"].keys():
                # nothing to do as this command was user entered
                return

        cmd = diff_walk_data[1]
        cmd_prop = diff_walk_data[3]
        if diff_walk_data[4] == delete:
            model_attr = diff_walk_data[5]
            try:
                del self.olddata[cmd][cmd_prop][model_attr]
            except KeyError:
                pass

    def merge_data(self,):
        """
        This merge only handles updates to
        commands
        listattrs
        createwithdefaults
        :return:
        """
        update_list = []
        for diff_walk_data in self.diff_tree_walk_generator(self.data_diff):
            # pp.pprint(self.data_diff)
            update_list.append(diff_walk_data)
            print 'attr change:', self.model_file, diff_walk_data
            # lets walk the data

        attr_insert_list = []
        for diff_walk_data in update_list:
            try:
                # updating a command
                if diff_walk_data[1] == "commands":
                    model_attr = diff_walk_data[5]
                    if model_attr == "type":
                        continue
                    if diff_walk_data[4] == update:
                        self.update_model_command_attribute(model_attr, diff_walk_data)
                    elif diff_walk_data[4] == insert and \
                            diff_walk_data[5] not in attr_insert_list:
                        attr_insert_list.append(model_attr)
                        insert_data = [x for x in update_list if len(x) >= 6 and x[4] == insert and x[5] == model_attr]
                        self.insert_model_command_attribute(model_attr, insert_data)
                    elif diff_walk_data[4] == delete:
                        self.delete_model_command_attribute(model_attr, diff_walk_data)
                elif diff_walk_data[1] == "listattrs":
                    if diff_walk_data[0] == update:
                        addvalues = frozenset(diff_walk_data[2]).difference(self.olddata["listattrs"])
                        delvalues = frozenset(self.olddata["listattrs"]).difference(diff_walk_data[2])
                        for x in delvalues:
                            self.olddata["listattrs"].remove(x)
                        for x in addvalues:
                            self.olddata["listattrs"].append(x)

                elif diff_walk_data[1] == "createwithdefault":
                    self.olddata["createwithdefault"][diff_walk_data[3]] = diff_walk_data[4]
                elif diff_walk_data[1] == "cmd_to_subcmd":
                    if "cmd_to_subcmd" not in self.olddata:
                        self.olddata.update({diff_walk_data[1]: {}})
            except Exception as e:
                print e, diff_walk_data

        with open(self.path + self.model_file,  'w') as f:
            json.dump(self.olddata, f, indent=2, sort_keys=True)


class SchemaModelMerge(ModelMergeCommon):

    def update_value_command_attribute(self, diff_walk_data_list):

        for diff_walk_data in diff_walk_data_list:
            try:
                # [update, u'acl', update, u'properties', update, u'value', update, u'properties', update, u'AclName',
                # update, u'properties', update, u'cliname', update, u'default', u'acl']
                model = diff_walk_data[1]
                value_attr_key_action = diff_walk_data[8]
                value_attr = diff_walk_data[9]
                if value_attr_key_action == update:
                    self.olddata[model]["properties"]["value"]["properties"][value_attr]["properties"][
                            diff_walk_data[13]].update({diff_walk_data[15]: diff_walk_data[16]})
                elif value_attr_key_action == insert:
                    attr_data = {
                        value_attr: {"properties": {},
                                     "type": "object"}
                    }
                    for insert_data in diff_walk_data_list:
                        if insert_data[9] == value_attr and \
                                        insert_data[10] == "properties":
                            if insert_data[11] not in attr_data[value_attr]["properties"]:
                                attr_data[value_attr]["properties"].update(
                                    {insert_data[11]: {insert_data[12]: insert_data[13]}})
                            else:
                                attr_data[value_attr]["properties"][insert_data[11]].update(
                                    {insert_data[12]: insert_data[13]})

                    self.olddata[model]["properties"]["value"]["properties"].update(attr_data)

                elif value_attr_key_action == delete:
                    try:
                        del self.olddata[model]["properties"]["value"]["properties"][value_attr]
                    except KeyError:
                        pass
            except Exception as e:
                print e, diff_walk_data

    def merge_data(self,):
        """
        This merge only handles updates to
        commands
        listattrs
        createwithdefaults
        :return:
        """
        update_list = []
        for diff_walk_data in self.diff_tree_walk_generator(self.data_diff):
            # pp.pprint(self.data_diff)
            update_list.append(diff_walk_data)
            print 'attr change:', self.model_file, diff_walk_data
            # lets walk the data

        key_list_update = []
        for diff_walk_data in update_list:
            try:
                # updating a command
                model = diff_walk_data[1]
                action = diff_walk_data[2]
                key = diff_walk_data[3]
                key_data = diff_walk_data[4]
                # new attribute being added
                if action == insert:
                    # some new type of attribute?
                    self.olddata[model].update({key: key_data})
                elif action == update:
                    if key == "properties":
                        key = diff_walk_data[5]
                        if key == "cliname":
                            self.olddata[model]["properties"][key]["default"] = diff_walk_data[9]
                        elif key == "help":
                            self.olddata[model]["properties"][key]["default"] = diff_walk_data[9]
                        elif key == "value" and \
                                diff_walk_data[9] not in key_list_update:
                            attr_name = diff_walk_data[9]
                            key_list_update.append(attr_name)
                            insert_value_list = [x for x in update_list if len(x) >= 10 and
                                                 x[5] == "value" and x[9] == attr_name]
                            self.update_value_command_attribute(insert_value_list)
            except Exception as e:
                print e, diff_walk_data

        with open(self.path + self.model_file,  'w') as f:
            json.dump(self.olddata, f, indent=2, sort_keys=True)


class ModelMembersMerge(ModelMergeCommon):

    def merge_data(self,):
        """
        This merge only handles updates to
        commands
        listattrs
        createwithdefaults
        :return:
        """
        update_list = []
        for diff_walk_data in self.diff_tree_walk_generator(self.data_diff):
            # pp.pprint(self.data_diff)
            update_list.append(diff_walk_data)
            print 'attr change:', self.model_file, diff_walk_data
            # lets walk the data

        for diff_walk_data in update_list:
            try:
                # updating a command
                commands = diff_walk_data[1]
                command_attr_action = diff_walk_data[2]
                command_attr = diff_walk_data[3]
                if command_attr_action == insert:
                    subkey = diff_walk_data[4]
                    subkey_value = diff_walk_data[5]
                    print 'including attribute', command_attr, subkey, subkey_value
                    self.olddata[commands][command_attr].update({subkey: subkey_value})
                elif command_attr_action == delete:
                    try:
                        print 'deleting attribute', command_attr
                        del self.olddata[commands][command_attr]
                    except Exception as e:
                        print e, diff_walk_data
            except Exception as e:
                print e, diff_walk_data


class ModelMerge(ModelMergeCommon):

    def update_value_command_attribute(self, attr_name,  diff_walk_data_list):

        if self.model_file == "ArpGlobal.json":
            import ipdb; ipdb.set_trace()
        first_attr_key = None
        for diff_walk_data in diff_walk_data_list:
            if "value" not in self.olddata[diff_walk_data[1]]:
                return

            if first_attr_key is None:
                first_attr_key = self.olddata[diff_walk_data[1]]["value"].keys()[0]

            try:
                model = diff_walk_data[1]
                value_model_action = diff_walk_data[4]
                if value_model_action == update:
                    value_model_attr = diff_walk_data[7]
                    value_model_attr_value = diff_walk_data[8]

                    orig_value_model_attr_value = self.olddata[diff_walk_data[1]]["value"][attr_name][value_model_attr]
                    if value_model_attr == "cliname":
                        if self.olddata[diff_walk_data[1]]["cliname"] != orig_value_model_attr_value and \
                                first_attr_key == attr_name or attr_name in DYNAMIC_MODEL_ATTR_NAME_LIST:
                            print "cli name missmatch between base and value attr", \
                                self.olddata[model]["cliname"], orig_value_model_attr_value
                            print "reverting to default", value_model_attr_value
                            self.olddata[model]["value"][attr_name][value_model_attr] = \
                                value_model_attr_value
                            self.olddata[model]["cliname"] = value_model_attr_value
                elif value_model_action == insert:
                    #  TODO new attribute do we need to add it, need logic to check for now always adding
                    value_attr = diff_walk_data[5]
                    if value_attr not in self.olddata[model]["value"]:
                        self.olddata[model]["value"].update({value_attr: {diff_walk_data[6]: diff_walk_data[7]}})
                    else:
                        self.olddata[model]["value"][value_attr].update({diff_walk_data[6]: diff_walk_data[7]})
                elif value_model_action == delete:
                    value_attr = diff_walk_data[5]
                    try:
                        del self.olddata[model]["value"][value_attr]
                    except KeyError:
                        pass
            except Exception as e:
                print e, diff_walk_data

    def merge_data(self,):
        """
        This merge only handles updates to
        commands
        listattrs
        createwithdefaults
        :return:
        """
        update_list = []
        for diff_walk_data in self.diff_tree_walk_generator(self.data_diff):
            # pp.pprint(self.data_diff)
            update_list.append(diff_walk_data)
            print 'attr change:', self.model_file, diff_walk_data
            # lets walk the data

        key_list_update = []
        for diff_walk_data in update_list:
            try:
                # updating a command
                model = diff_walk_data[1]
                action = diff_walk_data[2]
                key = diff_walk_data[3]
                key_data = diff_walk_data[4]
                # new attribute being added
                if action == insert and key != "value":
                    # some new type of attribute?
                    self.olddata[model].update({key: key_data})
                elif action == update:
                    orig_key_data = self.olddata[model][key]
                    if key == "cliname" and orig_key_data == "":
                        self.olddata[model][key] = key_data
                    elif key == "help" and orig_key_data == "":
                        self.olddata[model][key] = key_data
                    elif key == "value" and \
                            diff_walk_data[5] not in key_list_update:
                        attr_name = diff_walk_data[5]
                        key_list_update.append(attr_name)
                        insert_value_list = [x for x in update_list if len(x) >= 6 and
                                             x[3] == "value" and x[5] == attr_name]
                        self.update_value_command_attribute(attr_name, insert_value_list)
            except Exception as e:
                print e, diff_walk_data

        with open(self.path + self.model_file,  'w') as f:
            json.dump(self.olddata, f, indent=2, sort_keys=True)


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
                                if (f, obj) not in schema_obj_to_file_list[key]:
                                    schema_obj_to_file_list[key].append((f, obj))
                                if not os.path.exists(model_obj_path + f):
                                    print_red("ERROR file %s exists in schema but not in model" % (f,))

                                with open(model_obj_path + f, 'r') as f3:
                                    modelobj = json.load(f3)
                                    if (f, modelobj) not in model_obj_to_file_list[key]:
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
                    json.dump(schemadata, f2, indent=2, sort_keys=True)

                with open(self.model_gen_path + f, 'r') as f3:
                    modeldata = json.load(f3)

                    print "copying file: ", self.model_gen_path + f, "to:", self.model_path + f
                    with open(self.model_path + f, 'w+') as f4:
                        # save the info
                        json.dump(modeldata, f4, indent=2, sort_keys=True)

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
            json.dump(showschemadata, f2, indent=2, sort_keys=True)
        with open(self.model_path + 'show.json', 'w') as f2:
            # save the info
            json.dump(showmodeldata, f2, indent=2, sort_keys=True)
        with open(self.schema_path + 'config.json', 'w') as f2:
            # save the info
            json.dump(configschemadata, f2, indent=2, sort_keys=True)
        with open(self.model_path + 'config.json', 'w') as f2:
            # save the info
            json.dump(configmodeldata, f2, indent=2, sort_keys=True)

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

        for objname, f_dict in self.gen_model_obj_to_file_list.iteritems():
            # new_model_files += list(frozenset(f_dict["Members"]).difference(self.model_obj_to_file_list[objname]))
            gen_file_list = [f for (f, data) in f_dict["Keys"]]
            file_list = [f for (f, data) in self.model_obj_to_file_list[objname]["Keys"]]
            new_model_files += list(frozenset(gen_file_list).difference(file_list))

        num_schema_files = len(new_schema_files)
        num_model_files = len(new_model_files)

        # get the json data files
        showschemadata, showmodeldata, configschemadata, configmodeldata = self.get_show_config_json_data()
        import ipdb; ipdb.set_trace()
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

    @staticmethod
    def merge_schema_gen_to_master_data(model_type, schema_path, f, olddata, newdata):
        data_diff = diff(olddata, newdata, syntax='explicit')
        if len(data_diff) > 0:
            # pp.pprint(data_diff)
            merge = SchemaModelMerge(schema_path, f, data_diff, olddata, newdata)
            if model_type == "Members":
                merge = SchemaModelMembersMerge(schema_path, f, data_diff, olddata, newdata)

            merge.merge_data()

    @staticmethod
    def merge_model_gen_to_master_data(model_type, model_path, f, olddata, newdata):
        data_diff = diff(olddata, newdata, syntax='explicit')
        if len(data_diff) > 0:
            # pp.pprint(data_diff)
            merge = ModelMerge(model_path, f, data_diff, olddata, newdata)
            if model_type == "Members":
                merge = ModelMembersMerge(model_path, f, data_diff, olddata, newdata)
            merge.merge_data()

    @staticmethod
    def get_existing_members_key_files(gen_file_list, file_list):
        existing_members_schema_files = []
        existing_keys_schema_files = []
        for objname, f_dict in gen_file_list.iteritems():
            gen_f_list = [f for (f, data) in f_dict["Keys"]]
            f_list = [f for (f, data) in file_list[objname]["Keys"]]
            mem_gen_f_list = [f for (f, data) in f_dict["Members"]]
            mem_f_list = [f for (f, data) in file_list[objname]["Members"]]

            # these are the files which are the same we need to see if we need to merge them
            existing_members_schema_files += list(frozenset(mem_gen_f_list).intersection(mem_f_list))
            existing_keys_schema_files += list(frozenset(gen_f_list).intersection(f_list))

        return existing_members_schema_files, existing_keys_schema_files

    @staticmethod
    def get_compare_file_list(existing_files, gen_file_list, file_list):
        compare_members_schema_files = {}
        compare_key_schema_files = {}
        for f in existing_files:
            for objname, f_dict in gen_file_list.iteritems():
                for fname, fdata in f_dict["Keys"]:
                    if f == fname:
                        compare_key_schema_files.update({f: [fdata, ]})
                for fname, fdata in f_dict["Members"]:
                    if f == fname:
                        compare_members_schema_files.update({f: [fdata, ]})

            for objname, f_dict in file_list.iteritems():
                for fname, fdata in f_dict["Keys"]:
                    if f == fname:
                        compare_key_schema_files[f].append(fdata)
                for fname, fdata in f_dict["Members"]:
                    if f == fname:
                        compare_members_schema_files[f].append(fdata)

        return compare_members_schema_files, compare_key_schema_files

    def merge_existing_model_file_changes(self, ):
        existing_members_schema_files, existing_keys_schema_files = \
            self.get_existing_members_key_files(self.gen_schema_obj_to_file_list,
                                                self.schema_obj_to_file_list)

        existing_members_model_files, existing_keys_model_files = \
            self.get_existing_members_key_files(self.gen_model_obj_to_file_list,
                                                self.model_obj_to_file_list)

        # dict of file comparison
        compare_members_schema_files, tmp1 = \
            self.get_compare_file_list(existing_members_schema_files,
                                       self.gen_schema_obj_to_file_list,
                                       self.schema_obj_to_file_list)

        tmp1, compare_key_schema_files = \
            self.get_compare_file_list(existing_keys_schema_files,
                                       self.gen_schema_obj_to_file_list,
                                       self.schema_obj_to_file_list)
        compare_members_model_files, tmp1 = \
            self.get_compare_file_list(existing_members_model_files,
                                       self.gen_model_obj_to_file_list,
                                       self.model_obj_to_file_list)

        tmp1, compare_key_model_files = \
            self.get_compare_file_list(existing_keys_model_files,
                                       self.gen_model_obj_to_file_list,
                                       self.model_obj_to_file_list)



        for f, (gen, master) in compare_members_schema_files.iteritems():
            print 'comparing schema member file:', f
            self.merge_schema_gen_to_master_data("Members", self.schema_path, f, master, gen)
        for f, (gen, master) in compare_members_model_files.iteritems():
            print 'comparing model member file:', f
            self.merge_model_gen_to_master_data("Members", self.model_path, f, master, gen)

        for f, (gen, master) in compare_key_schema_files.iteritems():
            print 'comparing schema key file:', f
            self.merge_schema_gen_to_master_data("Keys", self.schema_path, f, master, gen)
        for f, (gen, master) in compare_key_model_files.iteritems():
            print 'comparing model key file:', f
            self.merge_model_gen_to_master_data("Keys", self.model_path, f, master, gen)

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