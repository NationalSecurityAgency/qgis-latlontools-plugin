PLUGINNAME = latlontools
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = latLonTools.py __init__.py copyLatLonTool.py captureCoordinate.py zoomToLatLon.py settings.py multizoom.py mgrs.py showOnMapTool.py mapProviders.py tomgrs.py mgrstogeom.py digitizer.py util.py geom2field.py field2geom.py olc.py provider.py pluscodes.py utm.py coordinateConverter.py geohash.py maidenhead.py latLonFunctions.py captureExtent.py ups.py
EXTRAS = metadata.txt icon.png

deploy:
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vfr images $(PLUGINS)
	cp -vfr ui $(PLUGINS)
	cp -vfr doc $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
