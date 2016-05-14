#!/usr/bin/python
import copy
import jsonref
import sys
from jsonschema import Draft4Validator
import inspect
import pprint



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
except:
    try:
        # For Windows readline support go visit ...
        # https://launchpad.net/pyreadline
        import pyreadline
    except:
        USING_READLINE = False

pp = pprint.PrettyPrinter(indent=2)

class CommonCmdLine(object):

    configDict = {}
    def __init__(self, parent, switch_ip, schema_path, model_path, layer):
        if not USING_READLINE:
            self.completekey = None
        self.config = None
        self.parent = parent
        self.switch_ip = switch_ip
        self.switch_name = None
        self.model = None
        self.modelpath = model_path + layer
        self.schema = None
        self.schemapath = schema_path + layer
        self.baseprompt = "DEFAULT"
        self.setSchema()
        self.setModel()
        self.currentcmd = []
        valid = self.validateSchemaAndModel()

        if not valid:
            sys.stdout.write("schema and model mismatch")
            sys.exit(0)

    def getSdk(self):
        sdk = True
        parent = self.parent
        child = self

        def getparent(child):
            return child.parent

        # to prevent looping forever going to not accept
        # a tree larger than 10 levels
        root = None
        while root is None:
            # root node has no parent
            # and it holds the sdk
            if parent is None:
                root = child.sdk
            else:
                child = parent

            if not root:
                parent = getparent(child)

        sys.stderr("Unable to find SDK for to access node")
        return root

    def getSubCommand(self, key, commands):

        #sys.stdout.write("commands: %s\n\n key %s\n\n"% (commands, key))

        for k, v in commands.iteritems():
            if k == key:
                #sys.stdout.write("RETURN 1 %s\n\n"% (v))
                return v

            # looking for subcommand
            if type(v) in (dict, jsonref.JsonRef) and key in v:
                #sys.stdout.write("RETURN 2 %s\n\n"% (v.keys()))
                return v
        return None

    def isValueExpected(self, cmd, schema):
        if schema:
            #sys.stdout.write("\nisValueExpected: cmd %s schema %s\n" %(cmd, schema[cmd].keys()))
            return "value" in schema[cmd]["properties"]
        return False

    def getValue(self, attribute):

        return hattribute["value"]

    def getPrompt(self, model, schema):
        try:
            return model["prompt"]
        except KeyError:
            schema["properties"]["prompt"]["default"]


    def getCliName(self, attribute):
        #sys.stdout.write("getCliName: %s" %(attribute["cliname"],))
        return attribute["cliname"]

    def setSchema(self):

        with open(self.schemapath) as schema_data:
            self.schema = jsonref.load(schema_data)

        pp.pprint(self.schema)


    def setModel(self):

        with open(self.modelpath, "r") as json_model_data:
            self.model = jsonref.load(json_model_data)
            #pp.pprint(self.model)

    def validateSchemaAndModel(self):
        if self.model is None or self.schema is None:
            sys.exit(2)
        else:
            try:
                # lets validate the model against the json schema
                Draft4Validator(self.model, self.schema)
            except Exception as e:
                print e
                return False
        return True

    def default(self,):
        pass

    def do_quit(self, args):
        " Quiting FlexSwitch CLI"
        sys.stdout.write('Quiting Shell\n')
        sys.exit(0)

    def do_end(self, args):
        " Return to enable  mode"
        return

    def do_exit(self, args):

        self.prompt = self.baseprompt
        self.stop = True

    def do_where(self, args):

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

        def get_sdk_func_key_values(func):
            argspec = inspect.getargspec(func)
            getKeys = argspec.args
            lengthkwargs = len(argspec.defaults) if argspec.defaults is not None else 0
            if lengthkwargs > 0:
                getKeys = argspec.args[:-len(argspec.defaults)]

            # lets setup the argument list
            argumentList = []
            for k in getKeys:
                for v in self.config.keysDict.values():
                    if v['key'] == k:
                        argumentList.append(v['value'])
            return argumentList

        if self.config:
            sys.stdout.write("Applying Config:\n")
            # tell the user what attributes are being applied
            self.config.show()

            # get the sdk
            sdk = self.getSdk()

            funcObjName = self.config.name

            #lets see if the object exists, by doing a get first
            get_func = getattr(sdk, 'get' + funcObjName)
            update_func = getattr(sdk, 'update' + funcObjName)
            create_func = getattr(sdk, 'create' + funcObjName)

            argumentList = get_sdk_func_key_values(get_func)
            try:
                r = get_func(*argumentList)
                if r.status_code in sdk.httpSuccessCodes:
                    # update
                    kwargs = self.config.getSdkAll()
                    r = update_func(*argumentList, **kwargs)
                    if r.status_code not in sdk.httpSuccessCodes:
                        sys.stdout.write("command failed %s %s" %(r.status_code, r.json()))
                elif r.status_code == 404:
                    # create
                    kwargs = self.config.getSdkAll()
                    create_func(*argumentList, **kwargs)
            except Exception as e:
                sys.stdout.write("FAILED TO GET OBJECT: %s")

            # remove the configuration as it has been applied
            self.config.clear(None, None, all=True)

    def do_showunapplied(self, argv):
        sys.stdout.write("Unapplied Config")
        self.config.show()


    def do_clearunapplied(self, argv):
        sys.stdout.write("Clearing Unapplied Config")

        self.configDict = {}
