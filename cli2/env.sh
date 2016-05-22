if [ -z "$PYTHONPATH" ]; 
then
	 export PYTHONPATH=$SR_CODE_BASE/snaproute/src/flexSdk/py/:$SR_CODE_BASE/snaproute/src/test/tests/:$SR_CODE_BASE/snaproute/src/test/utils/:$SR_CODE_BASE/snaproute/src/test/setups/
else 
	 export PYTHONPATH=$PYTHONPATH:$SR_CODE_BASE/snaproute/src/flexSdk/py/:$SR_CODE_BASE/snaproute/src/test/tests/:$SR_CODE_BASE/snaproute/src/test/utils/:$SR_CODE_BASE/snaproute/src/test/setups/
fi;
