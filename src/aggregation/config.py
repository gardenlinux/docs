"""Configuration loading and saving for documentation aggregation."""

import json
import sys
from typing import List

from .models import _DEFAULT_MEDIA_DIRECTORIES, RepoConfig


def load_config(config_path: str) -> List[RepoConfig]:
    """
    Load and validate repository configuration.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        List of validated RepoConfig objects
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "repos" not in config:
            raise ValueError("Configuration must have 'repos' array")

        repos = []
        for repo_dict in config["repos"]:
            repo = RepoConfig.from_dict(repo_dict)
            repo.validate()
            repos.append(repo)

        return repos
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)


def save_config(config_path: str, repos: List[RepoConfig]) -> None:
    """
    Save repository configuration to JSON file.

    Args:
        config_path: Path to JSON configuration file
        repos: List of RepoConfig objects to save
    """
    # Build config dict
    config = {
        "repos": [
            {
                "name": repo.name,
                "url": repo.url,
                "docs_path": repo.docs_path,
                **({"target_path": repo.target_path} if repo.target_path else {}),
                **({"ref": repo.ref} if repo.ref else {}),
                **({"commit": repo.commit} if repo.commit else {}),
                **({"root_files": repo.root_files} if repo.root_files else {}),
                **({"structure": repo.structure} if repo.structure != "flat" else {}),
                **(
                    {"media_directories": repo.media_directories}
                    if repo.media_directories != list(_DEFAULT_MEDIA_DIRECTORIES)
                    else {}
                ),
                **({"target_map": repo.target_map} if repo.target_map else {}),
                **({"docs_paths": repo.docs_paths} if repo.docs_paths else {}),
            }
            for repo in repos
        ]
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
