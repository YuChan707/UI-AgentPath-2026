# data_ingestor — self-contained container tasks.
# This service keeps its OWN dtos/ copy (intentionally divergent — see dtos/README).
IMAGE := onlooker-data-ingestor

.DEFAULT_GOAL := help
.PHONY: help build run clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

build: ## Build the self-contained image (context = this folder)
	docker build -t $(IMAGE) .

run: ## Run the ingestor once (Census -> data/locations/*.json)
	docker run --rm --env-file .env -v $(PWD)/data:/app/data $(IMAGE)

clean: ## Remove caches
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
