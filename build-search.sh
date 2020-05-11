pyinstaller -F \
	    --hidden-import google-api-python-client \
	    --hidden-import pkg_resources.py2_warn \
	    search.py
