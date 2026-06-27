# embeding-service — self-contained container tasks.
IMAGE := embeding-service
PORT  := 8100

.DEFAULT_GOAL := help
.PHONY: help vendor build run dapr clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

vendor: ## Re-vendor the Dapr contracts from the canonical root dtos/
	cp ../dtos/messages.py contracts.py
	@echo "✓ contracts.py vendored from ../dtos/messages.py"

build: ## Build the self-contained image (context = this folder)
	docker build -t $(IMAGE) .

run: ## Run the image standalone (no Dapr; for a quick smoke test)
	docker run --rm --env-file .env -p $(PORT):$(PORT) $(IMAGE)

dapr: ## Run locally with a Dapr sidecar
	REDIS_HOST=localhost:6379 dapr run --app-id embeding-service --app-port $(PORT) \
		--resources-path components \
		-- uvicorn main:app --host 0.0.0.0 --port $(PORT)

clean: ## Remove caches
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
