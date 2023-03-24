mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))

REMOTE = sholden@opal5.opalstack.com
HOME = /home/sholden
PROJECT = testing
APPDIR = ${HOME}/apps/${PROJECT}
ENVDIR = envs/${VERSION}
RELDIR = apps/${VERSION}
PORT_NO = "no_port#_provided"
PYTHON = $(mkfile_dir).reportlab/bin/python
JINJA = $(mkfile_dir).reportlab/bin/jinja

report:
	echo APPDIR: ${APPDIR} ENVDIR: ${ENVDIR} RELDIR: ${RELDIR} PROJECT: ${PROJECT} VERSION: ${VERSION} PORT_NO: ${PORT_NO}

create:
	${PYTHON} create_app.py ${PROJECT}

deploy:
	ssh ${REMOTE} " \
                cd ${APPDIR} ; \
		mkdir -p apps ; \
		mkdir -p envs  ; \
		mkdir -p tmp && rm -rf tmp/*"
	scp -r release/ ${REMOTE}:${APPDIR}/${RELDIR}
	ssh ${REMOTE} "cd ${APPDIR} ; \
		chmod +x kill start stop ; \
		python3.10 -m venv ${ENVDIR} ; \
		source ${ENVDIR}/bin/activate ; \
		pip install -r ${RELDIR}/requirements.txt ; \
		rm -f myapp ; ln -s ${RELDIR} myapp ; \
		rm -f env ; ln -s ${ENVDIR} env ; \
		ln -sf /home/sholden/bin/uwsgi env/bin"
