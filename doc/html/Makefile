# Makefile to build html pages for the metpx site.
# The files are generated using a special template and are not useful without the accompanying .css and .js files

MAKE = make
VERSION = $(shell grep __version__ ../../sarra/__init__.py | sed -e 's/"//g' | cut -c14-)
DATE = $(shell date "+%B %Y")

HTML_SRCS = $(wildcard ../*.rst)
HTML_TRGT = $(patsubst ../%.rst,%.html,$(HTML_SRCS))

SVG_SRCS = $(wildcard ../*.dia)
SVG_TRGT = $(patsubst ../%.dia,%.svg,$(SVG_SRCS))

TARGETS = $(HTML_TRGT) $(SVG_TRGT)

default: $(TARGETS) 
 
%.svg: ../%.dia
	dia -t svg $<

img:
	cp ../*.gif .

# In the html build, the TEMPLATE is provided on the command line
# see site/Makefile
%.html: ../%.rst	
	rst2html --link-stylesheet --stylesheet=css/bootstrap.min.css,css/metpx-sidebar.css $(TEMPLATE) $< $@
	sed -i 's/&\#64;Date&\#64;/$(DATE)/' $@
	sed -i 's/&\#64;Version&\#64;/$(VERSION)/' $@
	sed -i 's/<a class="toc-backref" .*">\(.*\)<\/a>/\1/' $@	
	sed -i 's/<div class="danger">/<div class="alert alert-danger" role="alert">/' $@
	sed -i 's/<p class="first admonition-title">!DANGER!<\/p>//' $@
	sed -i 's/<div class="warning">/<div class="alert alert-warning" role="alert">/' $@
	sed -i 's/<p class="first admonition-title">Warning<\/p>//' $@
	sed -i 's/<div class="note">/<div class="alert alert-info" role="alert">/' $@
	sed -i 's/<p class="first admonition-title">Note<\/p>//' $@
ifeq ($(wildcard ../../../template.py),) 
	@echo "WARNING: template.py missing, html files may be incomplete"
else
	python ../../../template.py $@
endif
	sed -i 's/<img \(.*\)\/>/<div class="panel"><div class="panel-body"><img \1 class="img-responsive"\/><\/div><\/div>/' $@

clean: 
	rm -f $(TARGETS)
