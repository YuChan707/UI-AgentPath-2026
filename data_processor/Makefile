# data_processor — self-contained container tasks.
IMAGE := onlooker-data-processor

.DEFAULT_GOAL := help
.PHONY: help vendor build run clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

vendor: ## Re-vendor the schemas from the canonical root dtos/
	cp ../dtos/__init__.py ../dtos/data_ingestors.py ../dtos/data_processors.py dtos/
	@echo "✓ dtos/ vendored from ../dtos/"

build: ## Build the self-contained image (context = this folder)
	docker build -t $(IMAGE) .

run: ## Run the processor once (offline mock transport)
	docker run --rm --env-file .env $(IMAGE) python -m data_processor --transport mock

clean: ## Remove caches
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
