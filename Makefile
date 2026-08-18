.PHONY: help run build preview publish transform aggregate aggregate-repo aggregate-update-repo aggregate-repo-single aggregate-update-repo-single test-aggregate-local clean clean-projects clean-aggregated-git test test-unit test-integration check spelling linkcheck woke glossary glossary-check format

help:
	@echo "Garden Linux Documentation Hub - Available targets:"
	@echo ""
	@echo "  Development:"
	@echo "    run                    - Run docs development server"
	@echo "    build                  - Build documentation for test purposes"
	@echo "    transform              - Run transformation on aggregated docs (may leave work tree 'dirty')"
	@echo "    preview                - Preview production build locally"
	@echo "    publish                - Build documentation with transformation for publishing"
	@echo ""
	@echo "  Testing:"
	@echo "    test                   - Run full test suite (unit + integration)"
	@echo "    test-unit              - Run unit tests only"
	@echo "    test-integration       - Run integration tests only"
	@echo ""
	@echo "  Quality Checks:"
	@echo "    check                  - Run all quality checks (spelling, links, inclusive language)"
	@echo "    spelling               - Check spelling with codespell"
	@echo "    linkcheck              - Check links with lychee"
	@echo "    woke                   - Check inclusive language with woke"
	@echo "    glossary               - Process glossary links in documentation"
	@echo "    glossary-check         - Validate glossary structure"
	@echo ""
	@echo "  Documentation Aggregation:"
	@echo "    aggregate-local        - Aggregate from local repos (file:// URLs in repos-config.local.json)"
	@echo "    aggregate              - Aggregate from locked commits (repos-config.json)"
	@echo "    aggregate-update       - Fetch latest from remotes and update commit locks"
	@echo "    aggregate-repo         - Aggregate all repos, overrides scoped to REPO (usage: make aggregate-repo REPO=gardenlinux [REF=branch] [COMMIT=hash])"
	@echo "    aggregate-update-repo  - Same as aggregate-repo plus update commit locks"
	@echo "    aggregate-repo-single       - Aggregate only REPO (usage: make aggregate-repo-single REPO=gardenlinux [REF=branch] [COMMIT=hash])"
	@echo "    aggregate-update-repo-single - Aggregate only REPO and update its commit lock (same optional REF/COMMIT)"
	@echo ""
	@echo "  Utilities:"
	@echo "    clean                  - Clean aggregated docs and build artifacts"
	@echo ""

install:
	@echo "Installing dependencies..."
	pnpm install
	pip install git+https://github.com/gardenlinux/glrd.git@v4.1.0
	# Install python-gardenlinux-lib from the same commit the aggregation
	# documents (see repos-config.json). This keeps the installed gardenlinux
	# module in sync with the fetched source so Sphinx autodoc can import
	# gardenlinux.* (e.g. oci -> podman, distro_version -> semver) and generate
	# the CLI/API reference pages. Pinning an older release tag here drops
	# those deps and breaks the python-gardenlinux-lib-cli reference.
	pip install git+https://github.com/gardenlinux/python-gardenlinux-lib.git@4da13c46b04d531d0bccfb5cb882f8581564af3b
	pip install -r requirements.txt

# Documentation Aggregation
aggregate-local:
	@echo "Aggregating from local repositories (relative paths)..."
	python3 src/aggregate.py --config repos-config.local.json

aggregate:
	@echo "Aggregating documentation from locked source repositories..."
	python3 src/aggregate.py

aggregate-update:
	@echo "Aggregating documentation from latest source repositories..."
	python3 src/aggregate.py --update-locks

aggregate-repo:
	@if [ -z "$(REPO)" ]; then \
		echo "Error: REPO variable not set"; \
		echo "Usage: make aggregate-repo REPO=gardenlinux [REF=branch] [COMMIT=hash]"; \
		exit 1; \
	fi
	@echo "Aggregating all repositories with overrides scoped to: $(REPO)"
	python3 src/aggregate.py --repo $(REPO) \
		$(if $(REF),--override-ref $(REF)) \
		$(if $(COMMIT),--override-commit $(COMMIT))

aggregate-update-repo:
	@if [ -z "$(REPO)" ]; then \
		echo "Error: REPO variable not set"; \
		echo "Usage: make aggregate-update-repo REPO=gardenlinux [REF=branch] [COMMIT=hash]"; \
		exit 1; \
	fi
	@echo "Aggregating all repositories with overrides scoped to: $(REPO) (updating locks)"
	python3 src/aggregate.py --update-locks --repo $(REPO) \
		$(if $(REF),--override-ref $(REF)) \
		$(if $(COMMIT),--override-commit $(COMMIT))

aggregate-repo-single:
	@if [ -z "$(REPO)" ]; then \
		echo "Error: REPO variable not set"; \
		echo "Usage: make aggregate-repo-single REPO=gardenlinux [REF=branch] [COMMIT=hash]"; \
		exit 1; \
	fi
	@echo "Aggregating single repository: $(REPO)"
	python3 src/aggregate.py --repo $(REPO) --single \
		$(if $(REF),--override-ref $(REF)) \
		$(if $(COMMIT),--override-commit $(COMMIT))

aggregate-update-repo-single:
	@if [ -z "$(REPO)" ]; then \
		echo "Error: REPO variable not set"; \
		echo "Usage: make aggregate-update-repo-single REPO=gardenlinux [REF=branch] [COMMIT=hash]"; \
		exit 1; \
	fi
	@echo "Aggregating single repository: $(REPO) (updating lock)"
	python3 src/aggregate.py --repo $(REPO) --single --update-locks \
		$(if $(REF),--override-ref $(REF)) \
		$(if $(COMMIT),--override-commit $(COMMIT))

run:
	pnpm run docs:dev

build: install clean aggregate
	pnpm run docs:build

transform: glossary
	@echo "Transforming content. This may have lead to an unclean worktree and is completely normal."

publish: install clean aggregate glossary
	pnpm run docs:build

preview:
	pnpm run docs:preview

format:
	black src/ tests/
	isort src/ tests/

# Testing
test: test-unit test-integration
	@echo "All tests passed!"

test-unit:
	@echo "Running unit tests..."
	python3 -m pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	python3 -m pytest tests/integration/ -v

# Quality Checks
check: spelling linkcheck woke
	@echo "All quality checks passed!"

spelling:
	@echo "Running spelling checks..."
	@pnpm run docs:spelling

linkcheck:
	@echo "Running link checks..."
	@pnpm run docs:linkcheck

woke:
	@echo "Running inclusive language checks..."
	@pnpm run docs:woke

glossary:
	@echo "Processing glossary links..."
	@python3 src/aggregation/auto_glossary.py docs/

glossary-check:
	@echo "Validating glossary structure..."
	@python3 src/aggregation/auto_glossary.py docs/ --check

# Utilities
clean:
	@echo "Cleaning build artifacts and aggregated docs..."
	rm -rf docs/.vitepress/dist
	rm -rf docs/.vitepress/cache
	@# Clean aggregated (untracked) content from section directories, preserving git-tracked files
	@if [ -d .git ]; then \
		git clean -fdX docs/contributing/ docs/explanation/ docs/how-to/ docs/reference/ docs/tutorials/ 2>/dev/null || true; \
	else \
		rm -rf docs/contributing docs/explanation docs/how-to docs/reference docs/tutorials; \
	fi
	@echo "Clean complete!"
