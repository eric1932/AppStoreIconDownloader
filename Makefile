EXE_NAME=iconsearch

executable: source_venv
	pyinstaller -F \
		--add-data ".env:." \
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
	if [ ! -d ${HOME}/.local/bin ]; then mkdir -p ${HOME}/.local/bin; fi; \
	install dist/search ${HOME}/.local/bin/${EXE_NAME}

all: executable install

clean:
	rm -rf build dist
