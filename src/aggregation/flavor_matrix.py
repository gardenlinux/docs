"""Generate flavor matrix documentation from flavors.yaml and feature dependencies."""

from pathlib import Path

import yaml
from gardenlinux.features import Parser as FeaturesParser
from gardenlinux.flavors.parser import Parser as FlavorsParser


def get_flavor_list(gardenlinux_repo_dir: Path) -> dict | None:
    """Get flavor list by parsing flavors.yaml directly."""
    flavors_file = gardenlinux_repo_dir / "flavors.yaml"

    if not flavors_file.exists():
        print(f"Warning: flavors.yaml not found at {flavors_file}")
        return None

    try:
        # Read and parse the YAML file
        flavors_data = yaml.safe_load(flavors_file.read_text())

        # Use the FlavorsParser to get combinations
        flavors_parser = FlavorsParser(flavors_data)
        combinations = flavors_parser.filter()

        # Group by architecture
        by_arch = {}
        for arch, combination in combinations:
            if arch not in by_arch:
                by_arch[arch] = []
            by_arch[arch].append(combination)

        return by_arch
    except Exception as e:
        print(f"Error parsing flavors.yaml: {e}")
        return None


def generate_flavor_matrix_docs(docs_dir: Path, gardenlinux_repo_dir: Path) -> bool:
    """
    Generate flavor matrix page from flavors.yaml and feature dependencies.

    Args:
        docs_dir: The docs directory to write output to
        gardenlinux_repo_dir: Path to the fetched gardenlinux repository

    Returns:
        True if successful, False otherwise
    """
    print("\nGenerating flavor matrix documentation...")

    # Step 1: Get flavor list from flavors.yaml
    flavors_by_arch = get_flavor_list(gardenlinux_repo_dir)
    if flavors_by_arch is None:
        print("Warning: Could not parse flavors - skipping flavor matrix generation")
        return False

    # Step 2: Build features parser for recursive resolution
    features_dir = gardenlinux_repo_dir
    if not features_dir.exists():
        print(f"Warning: features directory not found at {features_dir}")
        return False

    try:
        features_parser = FeaturesParser(
            str(features_dir)
        )  # Default feature_dir_name is "features"
    except Exception as e:
        print(f"Failed to initialize features parser: {e}")
        return False

    # Step 3: Generate table rows
    rows = []
    for arch, flavors in flavors_by_arch.items():
        for flavor in flavors:
            # Strip the arch suffix (e.g., "aws-gardener_prod-amd64" -> "aws-gardener_prod")
            flavor_base = flavor.replace(f"-{arch}", "")

            # Explicit features from cname
            explicit = FeaturesParser.get_cname_as_feature_set(flavor_base)

            # Full recursive feature set
            try:
                all_features = features_parser.filter_as_list(flavor_base)
            except Exception as e:
                print(f"Warning: Failed to resolve features for {flavor_base}: {e}")
                all_features = explicit[:]

            # Recursive-only = all minus explicit
            recursive_only = [f for f in all_features if f not in explicit]

            rows.append(
                {
                    "flavor": flavor_base,
                    "arch": arch,
                    "explicit": explicit,
                    "recursive": recursive_only,
                }
            )

    # Step 4: Render markdown with hyperlinks
    def link(feature: str) -> str:
        return f"[{feature}](features/{feature}.md)"

    header = "| Flavor | Arch | Features | Recursive Features |\n"
    header += "|--------|------|----------|--------------------|"

    table_rows = []
    for row in sorted(rows, key=lambda r: (r["flavor"], r["arch"])):
        explicit_links = ", ".join(link(f) for f in row["explicit"])
        recursive_links = ", ".join(link(f) for f in row["recursive"])
        # Build anchor ID from the full flavor name (includes architecture)
        anchor_id = f"{row['flavor']}-{row['arch']}"
        # Display the flavor name without arch suffix (flavor_base)
        display_name = f"`{row['flavor']}`"
        table_rows.append(
            f"| <a id='{anchor_id}'></a> {display_name} | {row['arch']} | {explicit_links} | {recursive_links} |"
        )

    table = header + "\n" + "\n".join(table_rows)

    # Step 5: Append table to existing aggregated file (keeps frontmatter and content)
    output_file = docs_dir / "reference" / "flavor-matrix.md"
    content: str = ""
    if output_file.exists():
        try:
            existing_content = output_file.read_text()
            # Append table
            content = existing_content + f"""

{table}
"""
        except Exception as e:
            print(f"Warning: Could not read existing file: {e}")

    if not content:
        print(
            f"Warning: Read existing file '{output_file}', but file contents are empty!"
        )

    output_dir = docs_dir / "reference"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "flavor-matrix.md"

    output_file.write_text(content)
    print(f"  Updated: {output_file}")

    print("Flavor matrix generation complete.")
    return True
