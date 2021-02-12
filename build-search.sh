if [[ "$(printenv __CFBundleIdentifier)" = "com.jetbrains.pycharm"
    && -z "$(printenv LOGIN_SHELL)" ]]; then
  source venv/bin/activate
fi

# build
pyinstaller -F \
	    --hidden-import google-api-python-client \
	    --hidden-import pkg_resources.py2_warn \
	    search.py
