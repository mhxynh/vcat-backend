from pathlib import Path
import argparse
import sys


DEFAULT_SOURCE_TEMPLATE = Path("template.yaml")
DEFAULT_OUTPUT_TEMPLATE = Path(".aws-sam/docker-template.yaml")


def rewrite_code_uri(line: str, code_uri_prefix: str) -> str:
    stripped = line.strip()
    if not stripped.startswith("CodeUri:"):
        return line

    indent = line[: len(line) - len(line.lstrip())]
    value = stripped.split(":", 1)[1].strip()
    if not value.startswith("src"):
        return line

    return f"{indent}CodeUri: {code_uri_prefix}{value}\n"


def prepare_template(source_template: Path, output_template: Path, code_uri_prefix: str) -> None:
    lines = source_template.read_text().splitlines(keepends=True)
    updated = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if line.startswith("  CommonDependencyLayer:"):
            index += 1
            while index < len(lines):
                next_line = lines[index]
                is_next_resource = (
                    next_line.startswith("  ")
                    and not next_line.startswith("    ")
                    and next_line.rstrip().endswith(":")
                )
                if is_next_resource:
                    break
                index += 1
            continue

        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        is_common_layer_reference = line.strip() == "Layers:" and next_line in (
            "- Ref: CommonDependencyLayer",
            "- !Ref CommonDependencyLayer",
        )
        if is_common_layer_reference:
            index += 2
            continue

        updated.append(line)
        index += 1

    output_template.parent.mkdir(parents=True, exist_ok=True)
    output_template.write_text(
        "".join(rewrite_code_uri(line, code_uri_prefix) for line in updated)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE_TEMPLATE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_TEMPLATE))
    parser.add_argument("--code-uri-prefix", default="../")
    args = parser.parse_args()

    source_template = Path(args.source)
    output_template = Path(args.output)

    if not source_template.is_file():
        print(f"Could not find SAM template at {source_template}", file=sys.stderr)
        return 1

    prepare_template(source_template, output_template, args.code_uri_prefix)
    print(f"Prepared {output_template} for Docker local invoke image.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
