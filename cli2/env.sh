if [ -z "$PYTHONPATH" ]; 
then
	 export PYTHONPATH=$SR_CODE_BASE/snaproute/src/flexSdk/py/:$SR_CODE_BASE/snaproute/src/apps/cli2/
else 
	 export PYTHONPATH=$PYTHONPATH:$SR_CODE_BASE/snaproute/src/flexSdk/py/:$SR_CODE_BASE/snaproute/src/apps/cli2/
fi;
