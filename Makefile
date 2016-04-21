COMPS=cfgmon\

all: install

exe:;
	 
clean: $(COMPS)
	 $(foreach f,$^, make -C $(f) clean;)

install: $(COMPS)
	 $(foreach f,$^, make -C $(f) install;)

