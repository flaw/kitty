ifdef V
	VVAL=--verbose
endif
ifdef VERBOSE
	VVAL=--verbose
endif

ifdef FAIL_WARN
export FAIL_WARN
endif

all:
	python3 setup.py $(VVAL)

test:
	python3 setup.py $(VVAL) test

clean:
	python3 setup.py $(VVAL) clean

# A debug build
debug:
	python3 setup.py build $(VVAL) --debug

debug-event-loop:
	python3 setup.py build $(VVAL) --debug --extra-logging=event-loop

# Build with the ASAN and UBSAN sanitizers
asan:
	python3 setup.py build $(VVAL) --debug --sanitize

profile:
	python3 setup.py build $(VVAL) --profile

# Local macOS signing identity (certificate name/hash, or - for ad-hoc).
# Override through the environment/command line; set empty to skip signing.
SIGN_IDENTITY ?= Kitty Local Development
export SIGN_IDENTITY

.PHONY: app sign-app
app:
	python3 setup.py kitty.app $(VVAL)
	@if [ -n "$$SIGN_IDENTITY" ]; then $(MAKE) sign-app; fi

# Re-sign an existing bundle without rebuilding it.
sign-app:
	@test -n "$$SIGN_IDENTITY" || { echo 'Set SIGN_IDENTITY to a certificate name/hash, or - for ad-hoc signing' >&2; exit 1; }
	python3 sign-macos.py --identity "$$SIGN_IDENTITY" kitty.app

linux-package: FORCE
	rm -rf linux-package
	python3 setup.py linux-package

FORCE:

man:
	$(MAKE) -C docs man

html:
	$(MAKE) -C docs html

dirhtml:
	$(MAKE) -C docs dirhtml

linkcheck:
	$(MAKE) -C docs linkcheck

website:
	./publish.py --only website

docs: man html


develop-docs:
	$(MAKE) -C docs develop-docs


prepare-for-cross-compile: clean all
	python3 setup.py $(VVAL) clean --clean-for-cross-compile

cross-compile:
	python3 setup.py linux-package --skip-code-generation
	
