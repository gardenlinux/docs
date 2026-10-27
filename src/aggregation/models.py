"""Data models for documentation aggregation."""

from dataclasses import dataclass, field
from typing import Dict, List

_DEFAULT_MEDIA_DIRECTORIES = [".media", "assets"]


@dataclass
class RepoConfig:
    """Configuration for a single repository."""

    name: str
    url: str
    docs_path: str
    ref: str
    commit: str | None = None
    target_path: str = ""
    root_files: List[str] = field(default_factory=list)
    structure: str = "flat"
    media_directories: List[str] = field(default_factory=list)
    target_map: Dict[str, str] = field(default_factory=dict)
    docs_paths: List[str] = field(default_factory=list)

    @property
    def resolved_docs_paths(self) -> List[str]:
        """Documentation-relevant glob patterns for this repository.

        Returns the explicit ``docs_paths`` override when set, otherwise derives
        the patterns from ``docs_path`` and ``root_files``. Used by the docs CI
        to decide whether a pull request touched documentation.
        """
        if self.docs_paths:
            return list(self.docs_paths)
        return [f"{self.docs_path}/**", *self.root_files]

    @property
    def is_local(self) -> bool:
        """Check if this is a local file:// repository."""
        return self.url.startswith("file://")

    @property
    def is_remote(self) -> bool:
        """Check if this is a remote https:// repository."""
        return self.url.startswith("https://")

    @property
    def local_path(self) -> str:
        """Get local path by stripping file:// prefix."""
        return self.url[7:] if self.is_local else ""

    def validate(self) -> None:
        """Validate repository configuration."""
        if not (self.is_local or self.is_remote):
            raise ValueError(f"Invalid URL scheme for {self.name}: {self.url}")

        if self.is_remote and not self.ref:
            raise ValueError(f"Remote repository {self.name} must have 'ref' field")

    @classmethod
    def from_dict(cls, data: Dict) -> "RepoConfig":
        """Create RepoConfig from dictionary."""
        media_directories = data.get("media_directories")
        if media_directories is None:
            media_directories = list(_DEFAULT_MEDIA_DIRECTORIES)

        structure = data.get("structure", "flat")
        if not isinstance(structure, str):
            raise ValueError(
                f"Repository '{data.get('name')}': 'structure' must be a string "
                f"('flat' or 'sphinx'), got {type(structure).__name__}"
            )

        return cls(
            name=data["name"],
            url=data["url"],
            docs_path=data.get("docs_path", "docs"),
            target_path=data.get("target_path", ""),
            ref=data.get("ref") or "main",
            commit=data.get("commit"),
            root_files=data.get("root_files", []),
            structure=structure,
            media_directories=media_directories,
            target_map=data.get("target_map", {}),
            docs_paths=data.get("docs_paths", []),
        )


@dataclass
class AggregateResult:
    """Result of aggregating a single repository."""

    repo_name: str
    success: bool
    resolved_commit: str | None = None
