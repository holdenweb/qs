OPAL = sholden@opal5.opalstack.com
HOME = /home/sholden
SITENAME = production
PORT = 53765
APPDIR = apps/${SITENAME}
ENVDIR = envs/${VERSION}
RELDIR = apps/${VERSION}
PYTHON = python3.10

report:
	echo app: ${APPDIR} envs: ${ENVDIR} myapp: ${RELDIR}

init:
	for filename in stop start kill uwsgi.ini; \
	do \
		jinja -D sitename ${SITENAME} -D port $$(cat release/port_no) $$filename > release/$$filename ; \
		scp release/$$filename ${OPAL}:${APPDIR}/$$filename ; \
	done ; \
	ssh ${OPAL} " \
                cd ${APPDIR}/ ; \
		mkdir apps ; \
		mkdir envs ; \
		mkdir tmp ; \
		chmod +x kill start stop"


deploy:
	scp -r release/ ${OPAL}:${HOME}/${APPDIR}/${RELDIR}
	ssh ${OPAL} "cd ${APPDIR} ; \
		${PYTHON} -m venv ${ENVDIR} ; \
		source ${ENVDIR}/bin/activate ; \
		pip install -r ${RELDIR}/requirements.txt ; \
		rm -f myapp ; ln -s ${RELDIR} myapp ; \
		rm -f env ; ln -s ${ENVDIR} env ; \
		ln -s /home/sholden/bin/uwsgi env/bin"
