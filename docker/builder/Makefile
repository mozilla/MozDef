all:
	docker build -t mozdef_builder:latest .
	docker tag mozdef_builder mozdef/mozdef_builder:latest
	docker login
	docker push mozdef/mozdef_builder:latest
