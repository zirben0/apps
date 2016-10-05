DESTDIR=$(SR_CODE_BASE)/snaproute/src/out/bin
MODEL_DIR = $(SR_CODE_BASE)/snaproute/src/apps/cli2/models/cisco
SCHEMA_DIR = $(SR_CODE_BASE)/snaproute/src/apps/cli2/schema
MODEL_JSONS := $(foreach dir, $(MODEL_DIR), $(wildcard $(dir)/*.json))
SCHEMA_JSONS := $(foreach dir, $(SCHEMA_DIR), $(wildcard $(dir)/*.json))
PYTHON_CLI_FILES := $(foreach dir, ., $(wildcard $(dir)/*.py))
JSON_CLI_FILES := $(foreach dir, ., $(wildcard $(dir)/*.json))
MKDIR=mkdir -p


all: setup install

setup:
#	$(SR_CODE_BASE)/reltools/codegentools/gencode.sh
#	cp $(SR_CODE_BASE)/snaproute/src/models/objects/genObjectConfig.json genObjectConfig.json
#	@echo 'Creating CLI Model Schema'
#	source $(SR_CODE_BASE)/snaproute/src/apps/cli2/env.sh
#	python $(SR_CODE_BASE)/snaproute/src/apps/cli2/codegen/cliSchemaBuilder.py
	@cp $(SR_CODE_BASE)/snaproute/src/config/actions/configOrder.json configOrder.json

genclischema:
	@echo 'Creating CLI Model Schema'
	python $(SR_CODE_BASE)/snaproute/src/apps/cli2/codegen/cliSchemaBuilder.py

codegenclean:
	$(SR_CODE_BASE)/reltools/codegentools/cleangencode.sh

install:
	@$(MKDIR) $(DESTDIR)/apps/cli2/schema/
	@$(MKDIR) $(DESTDIR)/apps/cli2/models/cisco/
	@install $(PYTHON_CLI_FILES) $(DESTDIR)/apps/cli2/
	@install $(JSON_CLI_FILES) $(DESTDIR)/apps/cli2/
	@install $(MODEL_JSONS) $(DESTDIR)/apps/cli2/models/cisco/
	@install $(SCHEMA_JSONS) $(DESTDIR)/apps/cli2/schema/


