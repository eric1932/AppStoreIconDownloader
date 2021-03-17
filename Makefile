EXE_NAME=iconsearch

executable: source_venv
	pyinstaller -F \
	    --hidden-import google-api-python-client \
	    --hidden-import pkg_resources.py2_warn \
	    --bootloader-ignore-signals \
	    search.py

source_venv:
	( \
		source venv/bin/activate; \
		pip install -r requirements.txt; \
	)

install:
	install dist/search ${HOME}/bin/${EXE_NAME}

all: executable install
