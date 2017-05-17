PLUGINNAME = latlontools
PY_FILES = latLonTools.py __init__.py copyLatLonTool.py zoomToLatLon.py settings.py LatLon.py multizoom.py mgrs.py showOnMapTool.py mapProviders.py tomgrs.py mgrstogeom.py
EXTRAS = metadata.txt

deploy:
	mkdir -p $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)
	cp -vfr images $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)
	cp -vfr ui $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)
	cp -vfr doc $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)
	cp -vf helphead.html $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)/index.html
	python -m markdown -x markdown.extensions.headerid readme.md >> $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)/index.html
	echo '</body>' >> $(HOME)/.qgis3/python/plugins/$(PLUGINNAME)/index.html

