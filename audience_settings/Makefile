# audience-settings — self-contained UiPath agent container.
IMAGE := audience-settings
PORT  := 8102

.DEFAULT_GOAL := help
.PHONY: help vendor build run dapr uipath-init uipath-pack clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

vendor: ## Re-vendor the Dapr contracts from the canonical root dtos/
	cp ../dtos/messages.py contracts.py
	@echo "✓ contracts.py vendored"

build: ## Build the self-contained image (context = this folder)
	docker build -t $(IMAGE) .

run: ## Run the image standalone (no Dapr; smoke test)
	docker run --rm --env-file .env -p $(PORT):$(PORT) $(IMAGE)

dapr: ## Run locally with a Dapr sidecar
	REDIS_HOST=localhost:6379 dapr run --app-id audience-settings --app-port $(PORT) \
		--resources-path components \
		-- uvicorn main:app --host 0.0.0.0 --port $(PORT)

uipath-init: ## Generate the UiPath agent schemas
	uipath init

uipath-pack: ## Package the agent for UiPath Orchestrator
	uipath pack

clean: ## Remove caches
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
