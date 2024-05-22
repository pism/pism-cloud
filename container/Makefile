TAG=ckhrulev/pism-for-aws

image: Dockerfile
	docker build -t ${TAG} -f $^ .

run: image
	docker run --cap-add=sys_nice --rm -it \
		--entrypoint /bin/bash \
		-v ${HOME}/.aws:/home/worker/.aws \
		-v ${PWD}/:/home/worker/local \
		${TAG}
