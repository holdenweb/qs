OPAL = sholden@opal5.opalstack.com
APPDIR = /home/sholden/apps/holdenweb_flask
ENVDIR = ${APPDIR}/envs/${VERSION}
RELDIR = ${APPDIR}/apps/${VERSION}
PYTHON = python3.11

#uwsgi.ini: uwsgi.j2 release.json
#	jinja -D version ${VERSION} uwsgi.j2 > release/uwsgi.ini

init:
	ssh ${OPAL} " \
                cd ${APPDIR}/ ; \
		mkdir apps ; \
		mkdir envs ; \
		mv myapp apps/orig ; \
		mv env envs/orig ; \
		ln -s envs/orig env ; \
		ln -s apps/orig myapp"

deploy:
	scp -r release/ ${OPAL}:${RELDIR}
	ssh ${OPAL} "${PYTHON} -m venv ${ENVDIR} ; \
		ln -s ../../envs/orig/bin/uwsgi ${ENVDIR}/bin ; \
		ln -s ../../envs/orig/bin/sqlformat ${ENVDIR}/bin ; \
		source ${ENVDIR}/bin/activate ; \
		pip install -r ${RELDIR}/requirements.txt ; \
 		echo "Directory:" ; pwd ; \
		rm ${APPDIR}/myapp ; ln -s ${RELDIR} ${APPDIR}/myapp ; \
		rm ${APPDIR}/env ; ln -s ${ENVDIR} ${APPDIR}/env"
