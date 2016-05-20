# CLI
This application implements a framework CLI for Snaproute flexswitch protocol stack.

The code base is based on python [cmdln](http://code.google.com/p/cmdln/).  Because this package is not apart of standard library, it has been copied over for use within this apps dir.

The intention of this CLI framework is to allow the user to create a json schema and json model to emulate other CLI's in production.  This will allow for an easy transition from traditional networking devices like Cisco, Juniper, Arista, etc.  Now it should be noted that there is a lot of manual work in order to create this feel by editing the various json model files, or even in some cases the schema if it does not fit the needs of the user; more on this later.

The backend takes advantage of flexswitch [SDK](https://github.com/SnapRoute/flexSdk/blob/master/py/flexswitchV2.py) and [SDK Print](https://github.com/SnapRoute/flexSdk/blob/master/py/flexprint.py)

## Getting Started
Running the CLI requires that you tell it the path of the schema being used and which model being used.   The cli will verify that the two are compatible by running [jsonschema](https://pypi.python.org/pypi/jsonschema) more specifically Draft4Validator.  In some cases if you wish to run the cli against a remote device than an option to supply the ip address is available, if it is not supplied then "127.0.0.1" will be used.

### Example help
```
python snap_cli.py -h
Usage: snap_cli.py [options]

Options:
  -h, --help            show this help message and exit
  -s SWITCH_IP, --switch=SWITCH_IP
                        Switch IP to run the cli against
  -m CLI_MODEL_PATH, --model=CLI_MODEL_PATH
                        Path to the cli model to be used
  -j CLI_SCHEMA_PATH, --jschema=CLI_SCHEMA_PATH
                        Path to the cli model to be used

```

## Writing a model
The JSON schema is very simplistic in this first draft but the basic elements which are used by the cli are below
Some helpful json schema references for syntax:
- http://json-schema.org/
- http://usingjsonschema.com/assets/UsingJsonSchema_20140814.pdf

For now the cli only takes advantage of $ref, oneOf, and required

### Common keys within schema/model
```
cliname  - what name a given attribute or tree leaf should display to the user
prompt   - what should be displayed on the prompt once the command has been entered
help     - description shown when typing 'help' or '?' against a command
commands - list of commands.  If a reference ($ref) is used then it is required that 'subcmd' be prefixed at the member key
objname  - used to tell the cli what flexswitch datamodel object the attributes is refering to.  This will also be used
           to lookup the appropriate create/delete/update/get/print from the SDK and SDK Print
```

### Example Structure of code
```
Base
  - prompt-prefix
  - prompt
  - cliname
  - commands
    - config
      - interface
      - vlan
      - router
    - show
```
Each "command" with commands should be of type object as the cli is expecting this format.  
Leaf nodes describe the various objects within the flexswitch datamodel.
### Example Schema Leaf node (Vlan Members)
```json
{
  "commands": {
    "type": "object",
    "description": "",
    "properties": {
      "UntagIntfList": {
        "type": "object",
        "properties": {
          "prompt": {
            "default": "",
            "type": "string"
          },
          "cliname": {
            "default": "untagintflist",
            "type": "string"
          },
          "help": {
            "default": "\tList of interface names or ifindex values to  be added as untagged members of the vlan",
            "type": "string"
          },
          "key": {
            "default": false,
            "type": "boolean"
          }
        }
      },
      "IntfList": {
        "type": "object",
        "properties": {
          "prompt": {
            "default": "",
            "type": "string"
          },
          "cliname": {
            "default": "intflist",
            "type": "string"
          },
          "help": {
            "default": "\tList of interface names or ifindex values to  be added as tagged members of the vlan",
            "type": "string"
          },
          "key": {
            "default": false,
            "type": "boolean"
          }
        }
      },
      "VlanId": {
        "type": "object",
        "properties": {
          "prompt": {
            "default": "",
            "type": "string"
          },
          "cliname": {
            "default": "vlanid",
            "type": "string"
          },
          "help": {
            "default": "\t802.1Q tag/Vlan ID for vlan being provisioned",
            "type": "string"
          },
          "key": {
            "default": true,
            "type": "boolean"
          }
        }
      }
    }
  },
  "objname": {
    "default": "Vlan",
    "type": "string",
    "descirption": "object name to which references these attributes"
  }
}

```
### Example Model Leaf Node (VlanMembers)
```
{
  "objname" : {
    "type" : "string",
    "descirption" : "object name to which references these attributes",
    "default" : "Vlan"
  },
  "commands" : {
    "IntfList": {
      "cliname":  "member-list"
    },
    "UntagIntfList": {
      "cliname": "untag-member-list"
    },
    "VlanId": {
      "cliname": "vlan"
    }
  }
}
```
