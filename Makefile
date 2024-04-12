build:
	docker build ./scripts -t lab3

run: build
	sudo docker run --rm lab3