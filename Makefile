OPAL = sholden@opal5.opalstack.com
HOME = /home/sholden
APPDIR = apps/holdenweb_flask
ENVDIR = envs/${VERSION}
RELDIR = apps/${VERSION}
PYTHON = python3.10

report:
	echo app: ${APPDIR} envs: ${ENVDIR} myapp: ${RELDIR}

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
	scp -r release/ ${OPAL}:${HOME}/${APPDIR}/${RELDIR}
	ssh ${OPAL} "cd ${APPDIR} ; \
		${PYTHON} -m venv ${ENVDIR} ; \
		ln -s ../../../envs/orig/bin/uwsgi ${ENVDIR}/bin ; \
		source ${ENVDIR}/bin/activate ; \
		pip install -r ${RELDIR}/requirements.txt ; \
 		echo "Directory:" ; pwd ; \
		rm myapp ; ln -s ${RELDIR} myapp ; \
		rm env ; ln -s ${ENVDIR} env"
