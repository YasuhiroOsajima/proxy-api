build_api:
	docker build -t proxy-api:0.1 -f build/Dockerfile_apiserver .

build_worker:
	docker build -t proxy-worker:0.1 -f build/Dockerfile_worker .

clean:
	for i in `docker images | awk /none/'{print $3}'`; do docker rmi $i; done
