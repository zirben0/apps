#!/usr/bin/python
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
# Class contains common methods used the various tree elements of the cli.
#
import copy
import jsonref
import sys
import os
import cmdln
from jsonschema import Draft4Validator
import pprint
import requests
import getpass
import snapcliconst
from tablePrint import indent, wrap_onspace_strict
from flexswitchV2 import FlexSwitch
from flexprint import FlexPrint

USING_READLINE = True
try:
    # For platforms without readline support go visit ...
    # http://pypi.python.org/pypi/readline/
    import readline
    import rlcompleter
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
except Exception as e:
    print "Exception rasied on import reason: %s" %(e,)

pp = pprint.PrettyPrinter(indent=2)


def line2argv(line):
    r"""Parse the given line into an argument vector.

        "line" is the line of input to parse.

    This may get niggly when dealing with quoting and escaping. The
    current state of this parsing may not be completely thorough/correct
    in this respect.

    >>> from cmdln import line2argv
    >>> line2argv("foo")
    ['foo']
    >>> line2argv("foo bar")
    ['foo', 'bar']
    >>> line2argv("foo bar ")
    ['foo', 'bar']
    >>> line2argv(" foo bar")
    ['foo', 'bar']

    Quote handling:

    >>> line2argv("'foo bar'")
    ['foo bar']
    >>> line2argv('"foo bar"')
    ['foo bar']
    >>> line2argv(r'"foo\"bar"')
    ['foo"bar']
    >>> line2argv("'foo bar' spam")
    ['foo bar', 'spam']
    >>> line2argv("'foo 'bar spam")
    ['foo bar', 'spam']

    >>> line2argv('some\tsimple\ttests')
    ['some', 'simple', 'tests']
    >>> line2argv('a "more complex" test')
    ['a', 'more complex', 'test']
    >>> line2argv('a more="complex test of " quotes')
    ['a', 'more=complex test of ', 'quotes']
    >>> line2argv('a more" complex test of " quotes')
    ['a', 'more complex test of ', 'quotes']
    >>> line2argv('an "embedded \\"quote\\""')
    ['an', 'embedded "quote"']

    # Komodo bug 48027
    >>> line2argv('foo bar C:\\')
    ['foo', 'bar', 'C:\\']

    # Komodo change 127581
    >>> line2argv(r'"\test\slash" "foo bar" "foo\"bar"')
    ['\\test\\slash', 'foo bar', 'foo"bar']

    # Komodo change 127629
    >>> if sys.platform == "win32":
    ...     line2argv(r'\foo\bar') == ['\\foo\\bar']
    ...     line2argv(r'\\foo\\bar') == ['\\\\foo\\\\bar']
    ...     line2argv('"foo') == ['foo']
    ... else:
    ...     line2argv(r'\foo\bar') == ['foobar']
    ...     line2argv(r'\\foo\\bar') == ['\\foo\\bar']
    ...     try:
    ...         line2argv('"foo')
    ...     except ValueError as ex:
    ...         "not terminated" in str(ex)
    True
    True
    True
    """
    line = line.strip()
    argv = []
    state = "default"
    arg = None  # the current argument being parsed
    i = -1
    WHITESPACE = '\t\n\x0b\x0c\r '  # don't use string.whitespace (bug 81316)
    while 1:
        i += 1
        if i >= len(line): break
        ch = line[i]

        if ch == "\\" and i+1 < len(line):
            # escaped char always added to arg, regardless of state
            if arg is None: arg = ""
            if (sys.platform == "win32"
                or state in ("double-quoted", "single-quoted")
               ) and line[i+1] not in tuple('"\''):
                arg += ch
            i += 1
            arg += line[i]
            continue

        if state == "single-quoted":
            if ch == "'":
                state = "default"
            else:
                arg += ch
        elif state == "double-quoted":
            if ch == '"':
                state = "default"
            else:
                arg += ch
        elif state == "default":
            if ch == '"':
                if arg is None: arg = ""
                state = "double-quoted"
            elif ch == "'":
                if arg is None: arg = ""
                state = "single-quoted"
            elif ch in WHITESPACE:
                if arg is not None:
                    argv.append(arg)
                arg = None
            else:
                if arg is None: arg = ""
                arg += ch
    if arg is not None:
        argv.append(arg)
    if not sys.platform == "win32" and state != "default":
        raise ValueError("command line is not terminated: unfinished %s "
                         "segment" % state)
    return argv



# overkill but hey in case we want to do more with this we can
class Authentication(cmdln.Cmdln):
    USERNAME_PROMPT = "username:"
    PASSWORD_PROMPT = "password:"
    def __init__ (self, switch_ip):
        cmdln.Cmdln.__init__(self)
        if not USING_READLINE:
            self.completekey = None

        #self.optparser = self.get_optparser()
        self.optparser = None
        self.options = None
        self.switch_ip = switch_ip
        self.username = None
        self.password = ''
        self.prompt = self.USERNAME_PROMPT
        self.cmdloop()

    def do_help(self, argv):
        return ''

    def precmd(self, argv):

        if len(argv) != 1:
            return ''

        if self.prompt == self.USERNAME_PROMPT:
            self.username = argv[0]
            self.prompt = self.PASSWORD_PROMPT
            while self.password == '':
                self.password = getpass.getpass("password:")

            sys.stdout.write("WARNING: Authentication not being done...\n")
            self.stop = True
            return ''

# this is not a terminating command
SUBCOMMAND_VALUE_NOT_EXPECTED = 1
# this is a terminating command which expects a value from user
SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE = 2
# this is a terminating command but no value is necessary
SUBCOMMAND_VALUE_EXPECTED = 3
# this subcommand is not part of this object
SUBCOMMAND_INVALID = 4


class CmdFunc(object):
    def __init__(self, objowner, origfuncname, func):
        self.name = origfuncname
        self.func = func
        self.objowner = objowner
        self.__name__ = origfuncname

        # lets save off the function attributes to the class
        # in case someone like cmdln access it (which it does)
        x = dir(func)
        y = dir(self.__class__)
        z = frozenset(x).difference(y)
        for attr in z:
            setattr(self, attr, getattr(func, attr))


    # allow class to be called as a method
    def __call__(self, *args, **kwargs):
        getattr(self.objowner, self.func.__name__)(*args, **kwargs)


class CommonCmdLine(cmdln.Cmdln):

    MODEL_COMMAND = False
    LOCAL_COMMAND = True

    configDict = {}
    def __init__(self, parent, switch_ip, schema_path, model_path, layer):

        cmdln.Cmdln.__init__(self)
        if not USING_READLINE:
            self.completekey = None
        self.objname = None
        # dependency on CmdLine that these are set after the init
        self.sdk = FlexSwitch(switch_ip, 8080)
        self.sdkshow = FlexPrint(switch_ip, 8080)
        self.config = None
        self.parent = parent
        self.switch_ip = switch_ip
        self.switch_name = None
        #self.model = None
        self.basemodelpath = model_path
        self.modelpath = model_path + layer
        #self.schema = None
        self.baseschemapath = schema_path
        self.schemapath = schema_path + layer
        self.baseprompt = "DEFAULT"
        self.currentcmd = []
        '''
        try:
            import readline
            self.old_completer = readline.get_completer()
            readline.set_completer(self.complete)
            if sys.platform == "darwin":
                readline.parse_and_bind("bind ? rl_complete")
            else:
                readline.parse_and_bind("?: complete_2")
        except ImportError:
            pass
        '''
    def complete_2(self, text, state):
        print 'hi'

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx>0:
                cmd, args, foo = self.parseline(line)
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            matches = compfunc(text, line, begidx, endidx)
            # lets add a space after the command when we know it is the last one
            if len(matches) == 1:
                if snapcliconst.COMMAND_DISPLAY_ENTER in matches:
                    # we want to show the user that they have reach the end of command tree
                    sys.stdout.write("\n%s\n" %(snapcliconst.COMMAND_DISPLAY_ENTER))
                    sys.stdout.write(self._str(self.prompt) + line)
                    sys.stdout.flush()
                self.completion_matches = [x + " " for x in matches if x != snapcliconst.COMMAND_DISPLAY_ENTER]
            else:
                self.completion_matches = matches
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def setupalias(self, cmdNameList):
        """
        Setup the aliases for each of the cmds this should be called as part of setupcommands
        :param cmdNameList
        :return:
        """
        ALIASES = 'aliases'
        cmdNameList = [""] + sorted(cmdNameList) + [""]

        def cp(x): return len(os.path.commonprefix(x))

        cmdDict = {cmdNameList[i]: 1 + max(cp(cmdNameList[i-1:i+1]), cp(cmdNameList[i:i+2])) for i in range(1, len(cmdNameList)-1) }

        for cmd, prefixlen in cmdDict.iteritems():
            func = getattr(self, 'do_' + cmd)
            if not hasattr(func, ALIASES):
                setattr(func, ALIASES, [])

            func.aliases = [cmd[:i+1] for i, ch in enumerate(cmd) if i >= prefixlen-1 and cmd[:i+1] != cmd]
            #print cmd, func.aliases

    def convertUserCmdToModelCmd(self, usercmd, cmdNameList):
        """
        Convert a partial user command to a model command
        :param cmdNameList - list of sub commands from the model
        :return:
        """
        if usercmd == "?":
            return "help"

        cmdNameList = [""] + sorted(cmdNameList) + [""]
        def cp(x): return len(os.path.commonprefix(x))


        cmdDict = {cmdNameList[i]: 1 + max(cp(cmdNameList[i-1:i+1]), cp(cmdNameList[i:i+2])) for i in range(1, len(cmdNameList)-1) }
        for cmd, prefixlen in cmdDict.iteritems():
            if usercmd in [cmd[:i+1] for i, ch in enumerate(cmd) if i >= prefixlen-1 and cmd[:i+1] != cmd]:
                return cmd
            elif usercmd == cmd:
                return cmd

        return None

    def find_func_cmd_alias(self, subname):
        """
        function used by do_<cmd> to edit the arg list so that we have the compelete names
        which should match the model
        :param subname:
        :return:
        """
        for f in dir(self.__class__):
            if f.startswith("do_"):
                func = getattr(self, f)
                if hasattr(func, 'aliases'):
                    fcmdname = func.__name__.replace("do_", "")
                    if subname in func.aliases or \
                            (len(func.aliases) == 0 and subname == fcmdname):
                        return fcmdname

        return subname

    def getRootAttr(self, attr):
        parent = self.parent
        child = self

        def getparent(child):
            return child.parent

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        rootAttr = None
        while rootAttr is None:
            # root node has no parent
            # and it holds the sdk
            if parent is None:
                rootAttr = getattr(child, attr)
            else:
                child = parent

            if not rootAttr:
                parent = getparent(child)
        return rootAttr

    def getSdk(self):
        return self.getRootAttr('sdk')

    def getSdkShow(self):
        return self.getRootAttr('sdkshow')

    def getIfIndexToIntfRef(self, ifIndex):
        num = ifIndex
        try:
            if type(ifIndex) in (unicode, str):
                num = int(str(ifIndex))
        except ValueError:
            return None

        data = self.getRootAttr('IfIndexToIntfRef')
        return data.get(num, None)

    def getIntfRefToIfIndex(self, intfRef):
        data = self.getRootAttr('IntfRefToIfIndex')
        return data.get(intfRef, None)

    def getShowObj(self,):
        return self.getObjByInstanceType('ShowCmd')

    def getConfigObj(self):
        return self.getObjByInstanceType('ConfigCmd')

    def getRootObj(self):
        return self.getObjByInstanceType('CmdLine')

    def getObjByInstanceType(self, instname):
        """
        Get object by walking the tree to find the instance
        For now we are using this to find the instance who
        has the attribute configList which contains all
        the config entries
        :return:
        """
        child = self
        config = None
        def getparent(child):
            return child.parent
        if child.__class__.__name__ == instname:
            config = child

        parent = getparent(child)
        while parent is not None and config is None:
            if parent.__class__.__name__ == instname:
                config = parent
            child = parent
            parent = getparent(child)
        return config

    def isSubCommandList(self, commandkey, commands, model=None):
        iscommandalist = False
        key = commandkey
        if model and type(model) in (dict, jsonref.JsonRef):
            key = self.getSchemaCommandNameFromCliName(commandkey, model)
            if not key:
                if 'commands' in model:
                    for cmd, submodel in model["commands"].iteritems():
                        if 'subcmd' in cmd and key is None:
                            key = self.getSchemaCommandNameFromCliName(commandkey, submodel)
                if [x for x in model.keys() if 'subcmd' in x]:
                    for cmd, submodel in model.iteritems():
                        if type(submodel) in (dict, jsonref.JsonRef):
                            for y in submodel.values():
                                if 'cliname' in y and y['cliname'] == commandkey:
                                    key = self.getSchemaCommandNameFromCliName(commandkey, submodel)

            if not key:
                key = commandkey

        if type(commands) in (dict, jsonref.JsonRef):
            for k, v in commands.iteritems():
                #print "subCommand: key %s k %s v %s\n\n" %(key, k, v)

                if k != key:
                     # looking for subcommand
                    if type(v) in (dict, jsonref.JsonRef):
                        if 'subcmd' in k:
                            listattrDict = dict(v['listattrs']) if 'listattrs' in v else {}
                            for kk, vv in v.iteritems():
                                if 'commands' in kk and 'properties' in vv and 'cliname' not in vv['properties']:
                                    for kkk, vvv in vv['properties'].iteritems():
                                        if 'subcmd' in kkk and kkk in listattrDict:
                                            iscommandalist = True

                                elif 'commands' in kk and 'cliname' not in vv:
                                    for kkk, vvv in vv.iteritems():
                                        if 'subcmd' in kkk and kkk in listattrDict:
                                            iscommandalist = True

        return iscommandalist
    # TODO write more readable logic to get a model commands sub command obj
    # This is a critical function as all complete_, and do_ functions use
    # this
    def getSubCommand(self, commandkey, commands, model=None):
        subList = []
        key = commandkey
        if model and type(model) in (dict, jsonref.JsonRef):
            key = self.getSchemaCommandNameFromCliName(commandkey, model)
            if not key:
                if 'commands' in model:
                    for cmd, submodel in model["commands"].iteritems():
                        if 'subcmd' in cmd and key is None:
                            key = self.getSchemaCommandNameFromCliName(commandkey, submodel)
                if [x for x in model.keys() if 'subcmd' in x]:
                    for cmd, submodel in model.iteritems():
                        if type(submodel) in (dict, jsonref.JsonRef):
                            for y in submodel.values():
                                if 'cliname' in y and y['cliname'] == commandkey and key is None:
                                    key = self.getSchemaCommandNameFromCliName(commandkey, submodel)

            if not key:
                key = commandkey

        if type(commands) in (dict, jsonref.JsonRef):

            for k, v in commands.iteritems():
                #print "subCommand: key %s k %s v %s\n\n" %(key, k, v)

                if k == key:
                    #sys.stdout.write("RETURN 1 %s\n\n"% (v))
                    subList.append(v)
                else:
                     # looking for subcommand
                    if type(v) in (dict, jsonref.JsonRef):

                        if key in ('?', 'help'):
                            subList.append(v)
                        # attribute
                        elif key in v:
                            subList.append(v)
                        # model subcmd
                        elif key in [vv['cliname'] for vv in v.values() if 'cliname' in vv]:
                            subList.append(v)
                        # model command
                        elif key in [self.getCliName(vv) for kk, vv in v.iteritems() if 'commands' in kk and 'cliname' in vv]:
                            subList.append(v)
                        #elif "commands" in v and key in [self.getCliName(vv) for vv in v["commands"].values() if 'cliname' in vv]:
                        #    subList.append(v)
                        elif key in [vv['properties']['cliname']['default'] for vv in v.values() if 'properties' in vv and 'cliname' in vv['properties']]:
                            subList.append(v)
                        # schema command
                        elif key in [vv['properties']['cliname']['default'] for kk, vv in v.iteritems() if 'commands' in kk and 'properties' in vv and 'cliname' in vv['properties']]:
                            subList.append(v)
                        #elif "commands" in v and key in [vv['properties']['cliname']['default'] for vv in v["commands"]["properties"].values()]:
                        #    subList.append(v
                        elif 'subcmd' in k:
                            listattrDict = dict(v['listattrs']) if 'listattrs' in v else {}
                            for kk, vv in v.iteritems():
                                if 'commands' in kk and 'properties' in vv and 'cliname' not in vv['properties']:
                                    for kkk, vvv in vv['properties'].iteritems():
                                        if 'subcmd' in kkk:
                                            # all commands are subcmds
                                            for kkkk, vvvv in vvv.iteritems():
                                                if kkkk == key:
                                                    subList.append(vvv)
                                                elif 'properties' in vvvv and 'cliname' in vvvv['properties'] and key == vvvv['properties']['cliname']['default']:
                                                    subList.append(vvv)
                                            # sub commands part of a leaf
                                            #elif kkk in listattrDict:
                                            #    subList.append(vvv)
                                        #elif key == kkk:
                                        #    subList.append(vvv)

                                elif 'commands' in kk and 'cliname' not in vv:
                                    for kkk, vvv in vv.iteritems():
                                        if 'subcmd' in kkk:
                                            # all commands are subcmds
                                            for kkkk, vvvv in vvv.iteritems():
                                                if kkk == key:
                                                    subList.append(vvv)
                                                elif 'cliname' in vvvv and key == vvvv['cliname']:
                                                    subList.append(vvv)
                                            # sub commands part of a leaf
                                            #elif kkk in listattrDict:
                                            #    subList.append(vvv)
                                        #elif key == kkk:
                                        #    subList.append(vvv)

                                elif kk == key:
                                    subList.append(vv)

        return subList

    def getchildrencmds(self, parentname, model, schema, issubcmd=False):

        cliHelpList = self.getchildrenhelpcmds(parentname, model, schema, issubcmd)

        return [ x[0] for x in cliHelpList if x[0] != snapcliconst.COMMAND_DISPLAY_ENTER]

    def getSchemaCommandNameFromCliName(self, cliname, model):
        for key, value in model.iteritems():

            if type(value) in (dict, jsonref.JsonRef):
                # branch
                if 'cliname' in value and cliname == value['cliname']:
                    return key
                else: # leaf
                    for k, v in value.iteritems():
                        if 'commands' in k:
                            if type(v) in (dict, jsonref.JsonRef):
                                for kk, vv in v.iteritems():
                                    if 'subcmd' in kk:
                                        return self.getSchemaCommandNameFromCliName(cliname, vv)
                                    else:
                                        if 'cliname' in vv and cliname == vv['cliname']:
                                            return kk
                        else:
                            if type(v) in (dict, jsonref.JsonRef):
                                for kk, vv in v.iteritems():
                                    if type(vv) in (dict, jsonref.JsonRef):
                                        if 'cliname' in vv and cliname == vv['cliname']:
                                            return kk

        return None


    def getCreateWithDefault(self, cliname, schema, model):

        schemaname = self.getSchemaCommandNameFromCliName(cliname, model)
        if schema:
            for k, schemaobj in snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema).iteritems():
                if "subcmd" in k:
                   for kk in schemaobj.keys():
                       if 'createwithdefault' in kk:
                           return schemaobj[kk]['default']

        return False

    def getchildrenhelpcmds(self, parentname, model, schema, issubcmd=False):
        """
        This function gets the help commands
        :param parentname:
        :return: list of tuples in the format of (model attribute name, cliname, help description)
        """

        cliHelpList = [[snapcliconst.COMMAND_DISPLAY_ENTER, "", self.LOCAL_COMMAND]] if self.cmdtype != snapcliconst.COMMAND_TYPE_SHOW and not issubcmd else []
        if schema:
            schemaname = self.getSchemaCommandNameFromCliName(parentname, model)
            if schemaname:
                for k, schemaobj in snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema).iteritems():
                    if "subcmd" in k:
                        modelobj = snapcliconst.GET_MODEL_COMMANDS(schemaname, model)[k] \
                                    if k in snapcliconst.GET_MODEL_COMMANDS(schemaname, model) else None
                        x = []
                        if modelobj and type(modelobj) in (dict, jsonref.JsonRef):
                            listattrDict = {}
                            if 'listattrs' in modelobj:
                                listattrDict = dict(modelobj['listattrs'])
                            for kk, vv in modelobj.iteritems():
                                # leaf node
                                if kk == "commands":
                                    if self.cmdtype != snapcliconst.COMMAND_TYPE_SHOW:
                                        for kkk, vvv in vv.iteritems():
                                            # this is a struct or list of structs to follow
                                            if kkk in listattrDict:
                                                if type(vvv) in (dict, jsonref.JsonRef):
                                                    for kkkk, vvvv in vvv.iteritems():
                                                        if 'cliname' in vvvv.keys():
                                                            x.append([listattrDict[kkk], vvvv['cliname'], None])
                                            else:
                                                x.append([kkk, self.getCliName(vvv) , self.getCliHelp(vvv)])
                                elif type(vv) == dict:
                                    x.append([kk, self.getCliName(vv), self.getCliHelp(vv)])
                        # did not find the name in the model lets get from schema
                        for val in x:
                            if val[1] is None or val[2] is None:
                                for kk, vv in schemaobj.iteritems():
                                    # leaf node
                                    if kk == "commands":
                                        if self.cmdtype != snapcliconst.COMMAND_TYPE_SHOW:
                                            for kkk, vvv in vv["properties"].iteritems():
                                                if kkk == val[0]:
                                                    if "properties" in vvv:
                                                        cliname, clihelp = self.getCliName(vvv["properties"]), self.getCliHelp(vvv["properties"])
                                                        if val[1] is None:
                                                            val[1] = cliname["default"]
                                                        else:
                                                            val[2] = clihelp["default"]

                                                        if val[1] != parentname:
                                                            cliHelpList.append((val[1], val[2], self.MODEL_COMMAND))
                                    elif "properties" in vv and "commands" in vv["properties"]:
                                        # todo need to get proper parsing to find the help
                                        cliname, clihelp = self.getCliName(vv["properties"]), self.getCliHelp(vv["properties"])
                                        if val[1] is None and cliname:
                                            val[1] = cliname
                                        elif clihelp:
                                            val[2] = clihelp["default"]
                                        if val[1] != parentname:
                                            cliHelpList.append((val[1], val[2], self.MODEL_COMMAND))
                            else:
                                cliHelpList.append((val[1], val[2], self.MODEL_COMMAND))

        # get all the internal do_<xxx> commands for this class
        if self.cmdtype not in (snapcliconst.COMMAND_TYPE_SHOW, snapcliconst.COMMAND_TYPE_DELETE) and not issubcmd:
            for f in dir(self):
                if f.startswith('do_') and f.replace('do_', '') not in [x[0] for x in cliHelpList]:
                    docstr = getattr(self, f).__doc__
                    cliHelpList.append((f.replace('do_', ''), docstr if docstr else "", self.LOCAL_COMMAND))
        return sorted(cliHelpList)

    def getValueMinMax(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema:
            if schemaname in schema and \
                "properties" in schema[schemaname] and \
                    "value" in schema[schemaname]["properties"] and \
                    'properties' in schema[schemaname]['properties']['value']:
                keys = [k for k, v in schema[schemaname]['properties']['value']['properties'].iteritems() if type(v) in (dict, jsonref.JsonRef)]
                #objname = schema[schemaname]['properties']['objname']['default']
                #sys.stdout.write("\nisValueExpected: cmd %s objname %s flex keys %s %s\n" %(cmd, objname, keys, schema[schemaname]['properties']['value']['properties']))
                minmax = [(v['properties']['argtype']['minimum'],
                           v['properties']['argtype']['maximum']) for k, v in schema[schemaname]['properties']['value']['properties'].iteritems()
                                            if 'properties' in v and 'argtype' in v['properties'] and 'minimum' in v['properties']['argtype'] and k in keys]
                if minmax:
                    return minmax[0]
        return None, None

    def getValueSelections(self, cmd, model, schema):
        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema:
            if schemaname in schema and \
                "properties" in schema[schemaname] and \
                    "value" in schema[schemaname]["properties"] and \
                    'properties' in schema[schemaname]['properties']['value']:
                keys = [k for k, v in schema[schemaname]['properties']['value']['properties'].iteritems() if type(v) in (dict, jsonref.JsonRef)]
                objname = schema[schemaname]['properties']['objname']['default']
                #sys.stdout.write("\nisValueExpected: cmd %s objname %s flex keys %s %s\n" %(cmd, objname, keys, schema[schemaname]['properties']['value']['properties']))
                selections = [v['properties']['argtype']['enum'] for k, v in schema[schemaname]['properties']['value']['properties'].iteritems()
                                            if 'properties' in v and 'argtype' in v['properties'] and 'enum' in v['properties']['argtype'] and k in keys]
                if selections:
                    return selections[0]
        return []

    def commandAttrsLoop(self, modelcmds, schemacmds):
        for attr, val in modelcmds.iteritems():
            yield (attr, val), (attr, schemacmds[attr])

    def isCommandLeafAttrs(self, modelcmds, schemacmds):
        return "commands" in modelcmds and "commands" in schemacmds

    def isLeafValueExpected(self, cliname, modelcmds, schemacmds):
        keys = []
        islist = False
        objname = None
        expected = SUBCOMMAND_INVALID
        help = ''
        for (mattr, mattrval), (sattr, sattrval) in self.commandAttrsLoop(modelcmds["commands"], schemacmds["commands"]["properties"]):

            if 'cliname' in mattrval and mattrval['cliname'] == cliname:
                help = ''
                if sattrval['properties']['key']['default']:
                    keys.append(sattr)
                    if not sattrval['properties']['isdefaultset']['default']:
                        expected = SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE
                elif 'enum' in sattrval['properties']['argtype']:
                    help = "/".join(sattrval['properties']['argtype']['enum']) + '\n'
                    if len(sattrval['properties']['argtype']['enum']) == 2:
                        expected = SUBCOMMAND_VALUE_EXPECTED
                elif 'type' in sattrval['properties']['argtype'] and \
                        snapcliconst.isnumeric(sattrval['properties']['argtype']['type']):
                    expected = SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE
                elif 'type' in sattrval['properties']['argtype'] and \
                        snapcliconst.isboolean(sattrval['properties']['argtype']['type']):
                    expected = SUBCOMMAND_VALUE_EXPECTED
                else:
                    expected = SUBCOMMAND_VALUE_NOT_EXPECTED

                objname = schemacmds['objname']['default']
                help += sattrval['properties']['help']['default']
                islist = sattrval['properties']['islist']['default']
        return (expected, objname, keys, help, islist)


    def getModelDefaultAttrVal(self, cliname, schemaname, model, schema, delcmd=False):

        # touching an attribute within this command tree, but we need to find out which subcmd contains
        # the attribute
        if schemaname in model or "commands" in model:
            for modelkeys, modelcmds in snapcliconst.GET_MODEL_COMMANDS(schemaname, model).iteritems():
                schemacmds = snapcliconst.GET_SCHEMA_COMMANDS(schemaname, schema)[modelkeys]
                #leaf attr model
                if self.isCommandLeafAttrs(modelcmds,schemacmds):
                    for (mattr, mattrval), (sattr, sattrval) in self.commandAttrsLoop(modelcmds["commands"], schemacmds["commands"]["properties"]):
                        if 'cliname' in mattrval and mattrval['cliname'] == cliname:
                            isDefaultSet = snapcliconst.getSchemaCommandAttrIsDefaultSet(sattrval)
                            defaultArg = snapcliconst.getSchemaCommandAttrDefaultArg(sattrval)
                            # we want opposite of default if boolean delete
                            # lets do the opposite of default value if enums length is 2
                            # or if we have a boolean value.
                            # this helps when setting string based boolean values
                            argtype = snapcliconst.getValueArgumentType(sattrval)
                            selections = snapcliconst.getValueArgumentSelections(sattrval)
                            if selections and \
                                    argtype and \
                                snapcliconst.isSelectionTypeNotNeeded(selections, argtype):

                                if delcmd:
                                    # lets determine the value based on whether this is a delcmd
                                    # or not
                                    # special case hack!!!
                                    if mattrval['cliname'] in ('shutdown', ):
                                        rv = list(frozenset([str(x).lower() for x in selections]).intersection(snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES))
                                        for k in selections:
                                            if rv and k.lower() == rv[0]:
                                                return k

                                    else:
                                        rv = list(frozenset([str(x).lower() for x in selections]).intersection(snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES))
                                        for k in selections:
                                            if rv and k.lower() == rv[0]:
                                                return k
                                else:
                                    # lets determine the value based on whether this is a delcmd
                                    # or not
                                    # special case hack!!!
                                    if mattrval['cliname'] in ('shutdown', ):
                                        rv = list(frozenset([str(x).lower() for x in selections]).intersection(snapcliconst.CLI_COMMAND_NEGATIVE_TRUTH_VALUES))
                                        for k in selections:
                                            if rv and k.lower() == rv[0]:
                                                return k
                                    else:
                                        rv = list(frozenset([str(x).lower() for x in selections]).intersection(snapcliconst.CLI_COMMAND_POSITIVE_TRUTH_VALUES))
                                        for k in selections:
                                            if rv and  k.lower() == rv[0]:
                                                return k
                                return None
                            elif snapcliconst.isboolean(argtype):

                                if delcmd:
                                    rv = False
                                else:
                                    rv = True
                                return rv

                            # setting default value
                            return defaultArg if isDefaultSet else None
        return None

    def isValueExpected(self, cmd, model, schema):
        '''
        Function used by most complete functions to determine based on the cmd
        and model/schema if a value is needed by the user or if the next cmd
        is another command.  If a value is expected this function may
        return valid values from model enums, so that the user knows what to
        add in the case an attribute is a selection attribute.
        :param cmd:
        :param model:
        :param schema:
        :return:
        '''

        schemaname = self.getSchemaCommandNameFromCliName(cmd, model)
        if schema and schemaname in schema:
            schemaValues = snapcliconst.getValueInSchema(schema[schemaname])
            if schemaValues:
                keys = [k for k, v in schemaValues.iteritems() if type(v) in (dict, jsonref.JsonRef)]
                help = ''
                expected = SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE
                # NOTE!!!! only one key supported!!!!!!
                for k, v in schemaValues.iteritems():
                    argtype = snapcliconst.getValueArgumentType(v)
                    islist = snapcliconst.isValueArgumentList(v)
                    enums = snapcliconst.getValueArgumentSelections(v)
                    if enums:
                        help = "/".join(enums) + '\n'
                        # special case don't need a value (default will be taken when applied)
                        if snapcliconst.isSelectionTypeNotNeeded(enums, argtype):
                            expected  = SUBCOMMAND_VALUE_EXPECTED
                    elif argtype:
                        if snapcliconst.isboolean(argtype):
                            expected = SUBCOMMAND_VALUE_EXPECTED

                    objname = snapcliconst.getSchemaObjName(schemaname, schema)
                    help += snapcliconst.getHelp(schemaname, model, schema)

                    return (expected, objname, keys, help, islist)

                # lets check to see if this schema is a command attribute schema
        return (SUBCOMMAND_VALUE_NOT_EXPECTED, None, [], "", False)

    def getValue(self, attribute):

        return attribute["value"]

    def getPrompt(self, model, schema):
        try:
            return model["prompt"]
        except KeyError:
            return None


    def getCliName(self, attribute):
        #print 'getCliName xxx:', attribute, type(attribute), 'cliname' in attribute, attribute["cliname"]
        return attribute["cliname"] if ((type(attribute) == dict) and ("cliname" in attribute)) else None

    def getCliHelp(self, attribute):
        return attribute["help"] if type(attribute) == dict and "help" in attribute else None

    def setSchema(self):

        with open(self.schemapath, 'r') as schema_data:
            sys.stdout.write("loading schema...\n")
            self.schema = None
            self.schema = jsonref.load(schema_data)
            # ENABLE THIS if you see problems with decode
            #pp.pprint(self.schema)


    def setModel(self):

        with open(self.modelpath, "rw+") as json_model_data:
            sys.stdout.write("loading model...\n")
            self.model = None
            self.model = jsonref.load(json_model_data)
            # ENABLE THIS if you see problems with decode
            #pp.pprint(self.model)

    def getSubModelSubSchemaListFromCommand(self, command, submodel, subschema):
        submodelList, subschemaList = self.getSubCommand(command, submodel), \
                            self.getSubCommand(command, subschema, submodel)
        if submodelList and subschemaList:
            return submodelList, subschemaList
        return [], []

    def convertKeyValueToDisplay(self, objName, key, value):
        #TODO this is a hack need a proper common mechanism to change special values
        returnval = value
        if key in snapcliconst.DYNAMIC_MODEL_ATTR_NAME_LIST:
            # lets strip the string name prepended
            returnval = returnval.replace(snapcliconst.PORT_NAME_PREFIX, "")
            # TODO not working when this is enabled so going have to look into this later
            #returnval = '1/' + returnval
        return str(returnval)


    def getCommandValues(self, objname, keys):

        # get the sdk
        try:
            sdk = self.getSdk()
            funcObjName = objname
            getall_func = getattr(sdk, 'getAll' + funcObjName + 's')
            if getall_func:
                objs = getall_func()
                if objs:
                    return [self.convertKeyValueToDisplay(objname, keys[0], obj['Object'][keys[0]]) for obj in objs]
        except Exception as e:
            sys.stdout.write("CommandValues: FAILED TO GET OBJECT: %s key %s reason:%s\n" %(objname, keys, e,))

        return []

    def display_help(self, argv, returnhelp=False):
        """
        This function is being used for two purposes:
        1) Display the current command help
        2) Retrieve the subcommands for a given level within a tree
        :param argv:
        :param returnhelp:
        :return:
        """
        if not returnhelp:
            mline = [self.objname] + argv[:-1]
        else:
            mline = [self.objname] + argv
        mlineLength = len(mline)
        submodel = self.model if hasattr(self, 'model') else self.modelList[0]
        subschema = self.schema if hasattr(self, 'schema') else self.schemaList[0]
        helpcommands = []
        if (mlineLength == 1 and not returnhelp) or returnhelp:
            helpcommands = self.getchildrenhelpcmds(self.objname, submodel, subschema)

        # advance to next submodel and subschema
        for i in range(1, mlineLength):
            if mline[i-1] in submodel:
                schemaname = self.getSchemaCommandNameFromCliName(mline[i-1], submodel)
                if schemaname:
                    submodelList, subschemaList = self.getSubModelSubSchemaListFromCommand(mline[i],
                                                                                      snapcliconst.GET_MODEL_COMMANDS(schemaname, submodel),
                                                                                      snapcliconst.GET_SCHEMA_COMMANDS(schemaname, subschema))
                    if submodelList and subschemaList:
                        for submodel, subschema in zip(submodelList, subschemaList):
                            (valueexpected, objname, keys, help, islist) = self.isValueExpected(mline[i], submodel, subschema)
                            if i == mlineLength - 1:
                                if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                    if self.cmdtype == snapcliconst.COMMAND_TYPE_SHOW:
                                        cmd = snapcliconst.COMMAND_DISPLAY_ENTER
                                    else:
                                        cmd = " ".join(argv[:-1])
                                    helpcommands = [[cmd, help, self.LOCAL_COMMAND]]
                                    tmphelpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema, issubcmd=True)
                                    if snapcliconst.COMMAND_TYPE_SHOW in self.cmdtype:
                                        helpcommands += tmphelpcommands
                                    else:
                                        if valueexpected == SUBCOMMAND_VALUE_EXPECTED_WITH_VALUE:
                                            values = self.getCommandValues(objname, keys)
                                            strvalues = ''
                                            if values:
                                                strvalues += ",".join(values)
                                            else:
                                                values = self.getValueSelections(mline[i], submodel, subschema)
                                                if values:
                                                    strvalues = ["%s" %(x,) for x in values]
                                                    strvalues += ",".join(strvalues)
                                                else:
                                                    min,max = self.getValueMinMax(mline[i], submodel, subschema)
                                                    if min is not None and max is not None:
                                                        strvalues += "%s-%s" %(min, max)
                                            helpcommands = [[cmd, strvalues + "\n" + help, self.MODEL_COMMAND]]
                                else:
                                    helpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema, issubcmd=True)
                            else:
                                if valueexpected != SUBCOMMAND_VALUE_NOT_EXPECTED:
                                    helpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema, issubcmd=True)
                                    if mline[i+1] in [cmd for (cmd, x, y) in helpcommands]:
                                        help = [h for (cmd, h, y) in helpcommands if mline[i+1] == cmd]
                                        if help:
                                            helpcommands = [[snapcliconst.COMMAND_DISPLAY_ENTER, help[0], self.LOCAL_COMMAND]]
                                    else:
                                        if snapcliconst.COMMAND_TYPE_SHOW in self.cmdtype:
                                            helpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema, issubcmd=True)
                                        else:
                                            helpcommands = [[snapcliconst.COMMAND_DISPLAY_ENTER, "", self.LOCAL_COMMAND]]
                                else:
                                    helpcommands = self.getchildrenhelpcmds(mline[i], submodel, subschema, issubcmd=True)

                    else:
                        if schemaname in submodel and 'commands' in submodel[schemaname]:
                            for mcmd, mcmdvalues in submodel[schemaname]['commands'].iteritems():
                                scmdvalues = subschema[schemaname]['properties']['commands']['properties'][mcmd]
                                if 'subcmd' in mcmd:
                                    if self.isCommandLeafAttrs(mcmdvalues, scmdvalues):
                                        if i == (mlineLength - 1): # value expected from attrs
                                            # reached attribute values
                                            for attr, attrvalue in mcmdvalues['commands'].iteritems():
                                                if attrvalue['cliname'] == mline[i]:
                                                    sattrvalue = scmdvalues['commands']['properties'][attr]
                                                    helpcommands.append([snapcliconst.getAttrCliName(attrvalue, sattrvalue),
                                                                         snapcliconst.getAttrHelp(attrvalue, sattrvalue),
                                                                         self.MODEL_COMMAND])
        if not returnhelp:
            self.printCommands(mline, helpcommands)

        return helpcommands

    def printCommands(self, argv, subcommands):

        COMMAND = 0
        HELP = 1
        MODEL_COMMAND_TYPE_MODEL_OR_LOCAL = 2

        OKGREEN = "\033[92m"
        GREENEND = "\033[0m"
        OKBOLD = "\033[00m"
        ENDBOLD = "\033[0m"

        def terminal_size():
            import fcntl, termios, struct
            h, w, hp, wp = struct.unpack('HHHH',
                fcntl.ioctl(0, termios.TIOCGWINSZ,
                struct.pack('HHHH', 0, 0, 0, 0)))
            return h, w

        height, width = terminal_size()

        labels = ('Command', 'Description',)
        rows = []

        rows.append(("control:", ""))
        for x in subcommands:
            if x[MODEL_COMMAND_TYPE_MODEL_OR_LOCAL]:
                rows.append(("  " + OKBOLD+x[COMMAND]+ENDBOLD, x[HELP]))

        rows.append(("context:", ""))
        for x in subcommands:
            # model command
            if not x[MODEL_COMMAND_TYPE_MODEL_OR_LOCAL]:
                rows.append(("  " + OKGREEN+x[COMMAND]+GREENEND, x[HELP]))
        width = (int(width) / 2) - 5

        print indent([labels]+rows, hasHeader=True, separateRows=True,
                     prefix=' ', postfix=' ', headerChar= '-', delim='    ',
                     wrapfunc=lambda x: wrap_onspace_strict(x,width))

        #print indent([labels]+rows, hasHeader=True, separateRows=True,
        #             prefix='| ', postfix=' |',
        #             wrapfunc=lambda x: wrap_onspace_strict(x,width))

    def prepareConfigTreeObjects(self, key, objname, createwithdefault, subcmd, model, schema, listAttrs):
        '''
        Based on the schema and model will fill in the default object parameters
        :param key:
        :param objname:
        :param subcmd:
        :param model:
        :param schema:
        :return: list of commands available from this leaf class
        '''

        def getObjNameAndCreateWithDefaultFromSchema(schema, model, objname, createwithdefault):
            objname = objname
            createwithdefault = createwithdefault
            if 'objname' in schema:
                objname = schema['objname']['default']
            if 'createwithdefault' in schema:
                createwithdefault = schema['createwithdefault']['default']
                if 'createwithdefault' in model:
                    createwithdefault = model['createwithdefault']

            return objname, createwithdefault

        cmdList = []
        cmdDict = {}
        tmpobjname = objname
        tmpcreatewithdefault = createwithdefault
        for k, v in schema.iteritems():
            if k == key:
                return v

            # TODO need to update function to ignore sub commands which are not terminating commands
            if k in model:
                tmpmodel = model[k]
                tmpobjname, tmpcreatewithdefault = getObjNameAndCreateWithDefaultFromSchema(v, tmpmodel, tmpobjname, tmpcreatewithdefault)

                # looking for subcommand attributes
                if "subcmd" in k and "commands" in v and type(v["commands"]) in (dict, jsonref.JsonRef):
                    listAttrs = v['listattrs'] if 'listattrs' in v else []
                    cmds = self.prepareConfigTreeObjects(key, tmpobjname, tmpcreatewithdefault, subcmd, tmpmodel["commands"], v["commands"]["properties"], listAttrs)
                    cmdList += cmds
                # looking for subsubcommand as this is an attribute that is an attribute,
                # this means that this is a reference to a struct or list of structs
                elif "subcmd" in k and type(v) in (dict, jsonref.JsonRef):
                    for kk, vv in tmpmodel.iteritems():
                        if kk in v:
                            subtmpschema = v[kk]['properties']
                            if 'objname' in subtmpschema:
                                tmpobjname = subtmpschema['objname']['default']

                            # a sub cmd is one which has a 'value' attribute defined
                            tmpsubcmd = None
                            if 'cliname' in vv:
                                tmpsubcmd = vv['cliname']

                            if "commands" in vv and len(vv) > 0:
                                attrDict = dict(listAttrs)
                                key = key

                                isList = False
                                if k in attrDict:
                                    key = attrDict[k]
                                    isList = True

                                # lets create the object, and tie it to the local object
                                cmds = self.prepareConfigTreeObjects(key,
                                                           tmpobjname,
                                                           tmpcreatewithdefault,
                                                           tmpsubcmd,
                                                           vv["commands"],
                                                           subtmpschema["commands"]["properties"],
                                                           listAttrs)
                                cmdList += cmds

                                # lets add the attribute to the subcmd
                                if key:
                                    cmdDict.update({tmpsubcmd : {'key': key,
                                                            'createwithdefaults' : tmpcreatewithdefault,
                                                            'subcommand' : subcmd,
                                                            'objname' :  objname,
                                                            'isattrkey': False,
                                                            'value': cmds,
                                                            'isarray': isList,
                                                            'type': tmpobjname}})

                else:
                    key = k
                    if 'subcmd' in key:
                        attrDict = dict(listAttrs)
                        key = attrDict[k]
                    cmdDict.update({tmpmodel['cliname'] : {'key': key,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
                                                    'isattrkey': v['properties']['key']['default'],
                                                    'value': v['properties']['defaultarg'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']}})

            elif 'properties' in v:
                cmdDict.update({v['properties']['cliname']['default'] : {'key': k,
                                                    'createwithdefaults' : tmpcreatewithdefault,
                                                    'subcommand' : subcmd,
                                                    'objname' : objname,
                                                    'isattrkey': v['properties']['key']['default'],
                                                    'value': v['properties']['defaultarg'],
                                                    'isarray': v['properties']['islist']['default'],
                                                    'type': v['properties']['argtype']}})

        if cmdDict:
            cmdList.append(cmdDict)

        return cmdList


    def do_quit(self, args):
        " Quiting FlexSwitch CLI.  This will stop the CLI session"
        sys.stdout.write('Quiting Shell\n')
        sys.exit(0)

    def do_end(self, args):
        "Return to enable mode"
        return

    def do_exit(self, args):
        """Exit current CLI tree position, if at base then will exit CLI"""
        self.prompt = self.baseprompt
        self.stop = True

    def do_where(self, args):
        """Display the current command path"""
        def getparent(child):
            return child.parent

        completecmd = self.currentcmd
        parent = self.parent
        if parent is not None:
            completecmd = parent.currentcmd + completecmd

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        while parent is not None:
            # root node has no parent
            # and it holds the sdk
            child = parent
            parent = getparent(child)
            if parent is not None:
                completecmd = parent.currentcmd + completecmd

        sys.stdout.write("\ncmd: %s\n\n" %(" ".join(completecmd,)))

    def do_apply(self, argv):
        """Apply current user unapplied config.  This will send provisioning commands to Flexswitch"""
        configObj = self.getConfigObj()
        if configObj:
            configObj.do_apply(argv)
            # lets move user back to config base
            # once the apply command has been entered
            if not self.__class__.__name__ == "ConfigCmd":
                self.do_exit(argv)

    def do_showunapplied(self, argv):
        """Display the currently unapplied configuration.  An optional 'full' argument can be supplied to show all objects which are pending not just valid provisioning objects"""
        configObj = self.getConfigObj()
        if configObj:
            configObj.do_showunapplied(argv)


    def do_clearunapplied(self, argv):
        """Clear the current pending config."""
        configObj = self.getConfigObj()
        if configObj:
            configObj.do_clearunapplied(argv)

        # need to ensure that we exit out of current config if we are
        # not already at config
        child = self
        if child.objname != "config":
            parent = child.parent
            while parent is not None:
                if parent.objname == "config":
                    self.do_exit([])
                    parent = None
                else:
                    self.do_exit([])
                    child = parent
                    parent = child.parent

    def precmd(self, argv):
        if len(argv) > 0:
            if argv[-1] in ('help', '?'):
                self.display_help(argv)
                return ''
        return argv
