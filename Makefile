COMPS=cfgmon\
	cli2

all: install

exe:;
	 
clean:;

install: $(COMPS)
	 $(foreach f,$^, make -C $(f) install;)

