TOP_SRCDIR=..
APP_ID=org.frescobaldi.Frescobaldi

.PHONY: all clean validate

all: $(APP_ID).desktop $(APP_ID).metainfo.xml

%.desktop: %.desktop.in
	msgfmt --desktop -d $(TOP_SRCDIR)/i18n/frescobaldi --template $< -o $@

%.metainfo.xml: %.metainfo.xml.in
	msgfmt --xml -d $(TOP_SRCDIR)/i18n/frescobaldi --template $< -o $@

validate:
	desktop-file-validate --no-hints $(APP_ID).desktop
	appstream-util validate $(APP_ID).metainfo.xml

clean:
	rm $(APP_ID).{desktop,metainfo.xml}
