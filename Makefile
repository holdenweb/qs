REMOTE = sholden@opal5.opalstack.com
HOME = /home/sholden
PROJECT = testing
APPDIR = ${HOME}/apps/${PROJECT}
ENVDIR = envs/${VERSION}
RELDIR = apps/${VERSION}
PORT_NO = "no_port#_provided"
PYTHON = python3.10

report:
	echo APPDIR: ${APPDIR} ENVDIR: ${ENVDIR} RELDIR: ${RELDIR} PROJECT: ${PROJECT} VERSION: ${VERSION} PORT_NO: ${PORT_NO}

create:
	python create_app.py ${PROJECT}

deploy:
	for filename in stop start kill uwsgi.ini; \
	do \
		jinja -D PROJECT ${PROJECT} -D port ${PORT_NO} $$filename | \
					ssh ${REMOTE} "cat > ${APPDIR}/$$filename" ; \
	done ; \
	ssh ${REMOTE} " \
                cd ${APPDIR} ; \
		mkdir -p apps && rm -rf apps/* ; \
		mkdir -p envs  ; \
		mkdir -p tmp && rm -rf tmp/*  ; \
		chmod +x kill start stop" ; \
	scp -r release/ ${REMOTE}:${APPDIR}/${RELDIR}
	ssh ${REMOTE} "cd ${APPDIR} ; \
		${PYTHON} -m venv ${ENVDIR} ; \
		source ${ENVDIR}/bin/activate ; \
		pip install -r ${RELDIR}/requirements.txt ; \
		rm -f myapp ; ln -s ${RELDIR} myapp ; \
		rm -f env ; ln -s ${ENVDIR} env ; \
		ln -sf /home/sholden/bin/uwsgi env/bin"
