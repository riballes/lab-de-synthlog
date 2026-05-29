VERSION := $(shell git describe --tags --abbrev=0 2>/dev/null || echo v0.0.0)
NEXT_PATCH := $(shell echo $(VERSION) | awk -F'[.v]' '{printf "v%s.%s.%s", $$2, $$3, $$4+1}')
NEXT_MINOR := $(shell echo $(VERSION) | awk -F'[.v]' '{printf "v%s.%s.0", $$2, $$3+1}')
NEXT_MAJOR := $(shell echo $(VERSION) | awk -F'[.v]' '{printf "v%s.0.0", $$2+1}')

.PHONY: help release release-minor release-major retry check version

help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check:  ## Run lint, typecheck, and tests
	uv run ruff check src/ tests/
	uv run mypy src/
	uv run pytest -v

version:  ## Show current and next versions
	@echo "Current:    $(VERSION)"
	@echo "Next patch: $(NEXT_PATCH)"
	@echo "Next minor: $(NEXT_MINOR)"
	@echo "Next major: $(NEXT_MAJOR)"

release:  ## Bump patch version and push tag (v0.1.0 -> v0.1.1)
	@echo "Releasing $(NEXT_PATCH)..."
	git tag $(NEXT_PATCH)
	git push origin $(NEXT_PATCH)
	@echo "Done. Tagged $(NEXT_PATCH)"

release-minor:  ## Bump minor version and push tag (v0.1.x -> v0.2.0)
	@echo "Releasing $(NEXT_MINOR)..."
	git tag $(NEXT_MINOR)
	git push origin $(NEXT_MINOR)
	@echo "Done. Tagged $(NEXT_MINOR)"

release-major:  ## Bump major version and push tag (v0.x.x -> v1.0.0)
	@echo "Releasing $(NEXT_MAJOR)..."
	git tag $(NEXT_MAJOR)
	git push origin $(NEXT_MAJOR)
	@echo "Done. Tagged $(NEXT_MAJOR)"

retry:  ## Delete and re-push the latest tag to retrigger deploy
	@echo "Retrying $(VERSION)..."
	git push origin :refs/tags/$(VERSION)
	git tag -d $(VERSION)
	git tag $(VERSION)
	git push origin $(VERSION)
	@echo "Done. Retagged $(VERSION)"
