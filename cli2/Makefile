all:
	$(SR_CODE_BASE)/reltools/codegentools/gencode.sh
	cp $(SR_CODE_BASE)/snaproute/src/models/objects/genObjectConfig.json genObjectConfig.json
	@echo 'Creating CLI Model Schema'
	python $(SR_CODE_BASE)/snaproute/src/apps/cli2/codegen/cliSchemaBuilder.py
	cp $(SR_CODE_BASE)/snaproute/src/apps/cfgmon/configOrder.json configOrder.json

genclischema:
	@echo 'Creating CLI Model Schema'
	python $(SR_CODE_BASE)/snaproute/src/apps/cli2/codegen/cliSchemaBuilder.py

codegenclean:
	$(SR_CODE_BASE)/reltools/codegentools/cleangencode.sh

