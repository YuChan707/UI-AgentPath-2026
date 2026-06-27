# ui-onlooker — self-contained container tasks (Next.js).
IMAGE := ui-onlooker
PORT  := 3000

.DEFAULT_GOAL := help
.PHONY: help install dev build run dapr

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

install: ## Install node deps
	npm install

dev: ## Run the Next.js dev server
	npm run dev

build: ## Build the self-contained image (context = this folder)
	docker build -t $(IMAGE) .

run: ## Run the image standalone
	docker run --rm --env-file .env.local -p $(PORT):$(PORT) $(IMAGE)

dapr: ## Run dev server with a Dapr sidecar (to publish document.uploaded)
	REDIS_HOST=localhost:6379 dapr run --app-id ui-onlooker --app-port $(PORT) \
		--resources-path components \
		-- npm run dev
