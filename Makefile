PLUGINNAME = latlontools
PY_FILES = latLonTools.py __init__.py copyLatLonTool.py zoomToLatLon.py settings.py LatLon.py multizoom.py mgrs.py
EXTRAS = metadata.txt

deploy:
	mkdir -p $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vfr images $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)
	cp -vfr ui $(HOME)/.qgis2/python/plugins/$(PLUGINNAME)

