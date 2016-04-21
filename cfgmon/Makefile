RM=rm -f
DESTDIR=$(SR_CODE_BASE)/snaproute/src/out/bin
MKDIR=mkdir -p
RSYNC=rsync -rupE

COMP_NAME=cfgmon
SRCS=monitor.py\

all: install 

install:
	@$(MKDIR) $(DESTDIR)/apps/cfgmon/
	@$(MKDIR) $(DESTDIR)/models/
	install $(SRCS) $(DESTDIR)/apps/cfgmon/ 
	install configOrder.json $(DESTDIR)/models/ 

