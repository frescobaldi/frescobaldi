# Disable `make` without targets.
all:

# Copy release notes from NEWS file and add them to metainfo file as XML.
.PHONY: news
news:
	appstreamcli news-to-metainfo NEWS linux/org.frescobaldi.Frescobaldi.metainfo.xml.in linux/org.frescobaldi.Frescobaldi.metainfo.xml.in
