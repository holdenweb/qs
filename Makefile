REMOTE = sholden@opal5.opalstack.com
HOME = /home/sholden
PROJECT = testing
TARGET = ${PROJECT}
APPDIR = ${HOME}/apps/${TARGET}
ENVDIR = envs/${VERSION}
RELDIR = apps/${VERSION}
PYTHON = python3.10

report:
	echo APPDIR: ${APPDIR} ENVDIR: ${ENVDIR} RELDIR: ${RELDIR} TARGET: ${TARGET} VERSION: ${VERSION}

create:
	python create_app.py ${TARGET}

deploy:
	for filename in stop start kill uwsgi.ini; \
	do \
		jinja -D PROJECT ${PROJECT} -D port $$(cat release/port_no) $$filename | \
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
		ln -s /home/sholden/bin/uwsgi env/bin"
