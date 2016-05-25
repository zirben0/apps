all:
	$(SR_CODE_BASE)/reltools/codegentools/gencode.sh
	@echo 'Creating CLI Model Schema'
	python $(SR_CODE_BASE)/snaproute/src/apps/cli2/codegen/cliSchemaBuilder.py

genclischema:
	@echo 'Creating CLI Model Schema'
	python $(SR_CODE_BASE)/snaproute/src/apps/cli2/codegen/cliSchemaBuilder.py

codegenclean:
	$(SR_CODE_BASE)/reltools/codegentools/cleangencode.sh

