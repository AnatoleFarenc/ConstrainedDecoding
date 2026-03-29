SRC = src
EXE = $(SRC)
VENV = .venv
PYTHON = $(VENV)/bin/python3
CACHE_DIR = $(CURDIR)/.uv_cache
HF_CACHE_DIR = $(CURDIR)/.hf_cache
HF_ENV = HF_HOME="$(HF_CACHE_DIR)" HUGGINGFACE_HUB_CACHE="$(HF_CACHE_DIR)/hub" TRANSFORMERS_CACHE="$(HF_CACHE_DIR)/transformers"


TRASH = $(SRC)/__pycache__ $(VENV) .mypy_cache __pycache__

FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs --no-error-summary

# ANSI codes
GREEN = \033[0;32m
RED = \033[0;31m
YELLOW = \033[0;33m
BOLD = \033[1m

SUCCESS = \033[1;92m
RESET = \033[0m

install:
	@echo "$(BOLD)Initializing project environment:$(RESET)"

	@echo "$(YELLOW)Creating virtual environment...$(RESET)"
	@UV_CACHE_DIR="$(CACHE_DIR)" UV_LINK_MODE=copy $(HF_ENV) \
		uv venv $(VENV) --clear > /dev/null 2>&1
	@echo "$(GREEN)Virtual environment setup complete$(RESET)"

	@bash -c '\
		UV_CACHE_DIR="$(CACHE_DIR)" UV_LINK_MODE=copy $(HF_ENV) UV_PROJECT_ENVIRONMENT="$(VENV)" \
		uv sync > /dev/null 2>&1 & pid=$$!; \
		spin="-\|/"; i=0; \
		while kill -0 $$pid 2>/dev/null; do \
			printf "\r$(YELLOW)[%s] Installing dependencies...$(RESET)" "$${spin:$$((i % 4)):1}"; \
			i=$$((i + 1)); \
			sleep 0.1; \
		done; \
		wait $$pid; \
		printf "\r$(GREEN)Installing dependencies... done$(RESET)\n"'

	@echo "$(GREEN)All dependencies successfully installed$(RESET)"
	@echo "\n$(SUCCESS)Project can now be run safely!$(RESET)"

run:
	@$(HF_ENV) $(PYTHON) -m $(EXE)

lint:
	@echo "$(BOLD)Verifying project source code:$(RESET)"

	@echo "$(YELLOW)Running flake8...$(RESET)"
	@$(HF_ENV) $(PYTHON) -m flake8
	@echo "$(GREEN)No norm errors found$(RESET)"

	@echo "\n$(YELLOW)Running mypy...$(RESET)"
	@$(HF_ENV) $(PYTHON) -m mypy . $(FLAGS)
	@echo "$(GREEN)No typing errors found$(RESET)"

	@echo "\n$(SUCCESS)Success: no errors found in source code!$(RESET)"

debug:
	@$(HF_ENV) $(PYTHON) -m pdb -m $(EXE) $(CONFIG)

clean:
	@echo "$(YELLOW)Initiating cleanup operation...$(RESET)"
	@found=0; \
	for i in $(TRASH); do \
		if [ -d "$$i" ]; then \
			echo " - Removed directory $(RED)'$$i'$(RESET)"; \
			found=1; \
		elif [ -e "$$i" ]; then \
			echo " - Removed file $(RED)'$$i'$(RESET)"; \
			found=1; \
		fi; \
	done; \
	if [ $$found -eq 0 ]; then \
		echo "$(GREEN)Nothing to clean :)$(RESET)"; \
	fi
	@rm -rf $(TRASH)
	@echo "$(SUCCESS)\nCleanup complete!$(RESET)"

clean_cache:
	@echo "$(YELLOW)Initiating cleanup cache operation...$(RESET)"
	@echo "$(RED) Removed: $(CACHE_DIR) $(HF_CACHE_DIR)$(RESET)"
	@rm -rf $(CACHE_DIR) $(HF_CACHE_DIR)
	@echo "$(SUCCESS)\nCleanup cache complete!$(RESET)"
