CLI_CODE_BASE = $(SR_CODE_BASE)/snaproute/src/apps/cli2/
SDK_CODE_BASE = $(SR_CODE_BASE)/snaproute/src/flexSdk/py/
all: pip clean 

pip:
	@echo 'Creating snap_cli pip install'
	@mkdir $(CLI_CODE_BASE)/pip/snap_cli
	@mkdir $(CLI_CODE_BASE)/pip/snap_cli/models
	@mkdir $(CLI_CODE_BASE)/pip/snap_cli/models/cisco
	@mkdir $(CLI_CODE_BASE)/pip/snap_cli/schema/
	@echo 'Copying over cli files'
	@cp $(CLI_CODE_BASE)/*.py  $(CLI_CODE_BASE)/pip/snap_cli/
	@cp $(CLI_CODE_BASE)/*.json  $(CLI_CODE_BASE)/pip/snap_cli/
	@cp $(CLI_CODE_BASE)/schema/*.json $(CLI_CODE_BASE)/pip/snap_cli/schema/
	@cp $(CLI_CODE_BASE)/models/cisco/*.json $(CLI_CODE_BASE)/pip/snap_cli/models/cisco/
	@echo 'Copying over flexSdk\py'
	@cp $(SDK_CODE_BASE)/*.py $(CLI_CODE_BASE)/pip/snap_cli/
	@echo 'Setting up main for snap_ci'
	@cp $(CLI_CODE_BASE)/pip/main.py $(CLI_CODE_BASE)/pip/snap_cli/__init__.py 
	@echo 'Building snap_cli tar file'
	@python $(CLI_CODE_BASE)/pip/setup.py sdist
	@cp $(CLI_CODE_BASE)/pip/dist/* $(CLI_CODE_BASE)/pip/

clean:
	@echo 'Cleaning snap_cli'
	@rm -rf $(CLI_CODE_BASE)/pip/dist
	@rm -rf $(CLI_CODE_BASE)/pip/snap_cli.egg-info
	@rm -rf $(CLI_CODE_BASE)/pip/snap_cli

