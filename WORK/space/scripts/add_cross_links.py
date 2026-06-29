import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONCEPTS_PATH = ROOT / "WORK" / "space" / "concepts.json"
PAGES_DIR = ROOT / "KIDBOOK" / "space"


def markdown_link_spans(line: str) -> list[tuple[int, int]]:
    return [match.span() for match in re.finditer(r"\[[^\]]+\]\([^)]+\)", line)]


def is_inside_existing_link(index: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def link_first_occurrence(text: str, aliases: list[str], target_file: str) -> str:
    in_code_block = False
    lines = text.splitlines(keepends=True)

    for line_index, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block or stripped.startswith("#"):
            continue

        existing_links = markdown_link_spans(line)

        for alias in aliases:
            pattern = re.compile(rf"(?<![\wА-Яа-яЁё])({re.escape(alias)})(?![\wА-Яа-яЁё])", re.IGNORECASE)

            for match in pattern.finditer(line):
                if is_inside_existing_link(match.start(), existing_links):
                    continue

                linked = f"[{match.group(1)}]({target_file})"
                line = line[: match.start()] + linked + line[match.end() :]
                lines[line_index] = line
                return "".join(lines)

    return text


def main() -> None:
    concepts = json.loads(CONCEPTS_PATH.read_text(encoding="utf-8"))

    for page_path in sorted(PAGES_DIR.glob("*.md")):
        page_text = page_path.read_text(encoding="utf-8")
        updated = page_text

        for concept in concepts:
            if concept["file"] == page_path.name:
                continue

            aliases = sorted(concept["aliases"], key=len, reverse=True)
            updated = link_first_occurrence(updated, aliases, concept["file"])

        page_path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
