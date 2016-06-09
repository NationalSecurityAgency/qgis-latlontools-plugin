PLUGINNAME = latlontools
PY_FILES = latLonTools.py __init__.py zoomToLatLon.py settings.py LatLon.py
EXTRAS = zoomicon.png copyicon.png settings.png metadata.txt
UI_FILES = zoomToLatLon.ui latLonSettings.ui
RESOURCE_FILES = resources.py

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%.py : %.qrc
	pyrcc4 -o $@ $<

deploy: compile
	mkdir -p $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)

clean:
	rm $(RESOURCE_FILES)

