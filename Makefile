TAG=pism/peak_memusage

image: Dockerfile
	docker build -t ${TAG} -f $^ .

run: image
	docker run --cap-add=sys_nice --rm -it \
		--entrypoint /bin/bash \
		${TAG}
