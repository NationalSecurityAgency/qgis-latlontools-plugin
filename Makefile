PLUGINNAME = latlontools
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = __init__.py captureCoordinate.py captureExtent.py coordinateConverter.py copyLatLonTool.py digitizer.py ecef.py field2geom.py geohash.py geom2field.py geom2wkt.py georef.py latLonFunctions.py latLonTools.py latLonToolsProcessing.py maidenhead.py mapProviders.py mgrs.py mgrstogeom.py multizoom.py olc.py pluscodes.py provider.py settings.py showOnMapTool.py tomgrs.py ups.py util.py utm.py wkt2layers.py zoomToLatLon.py
EXTRAS = metadata.txt icon.png LICENSE

deploy:
	mkdir -p $(PLUGINS)
	mkdir -p $(PLUGINS)/i18n
	cp -vf i18n/latlonTools_fr.qm $(PLUGINS)/i18n
	cp -vf i18n/latlonTools_zh.qm $(PLUGINS)/i18n
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vfr images $(PLUGINS)
	cp -vfr ui $(PLUGINS)
	cp -vfr doc $(PLUGINS)
	cp -vf helphead.html index.html
	python -m markdown -x extra readme.md >> index.html
	echo '</body>' >> index.html
	cp -vf index.html $(PLUGINS)/index.html
