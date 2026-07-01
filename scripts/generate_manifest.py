from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]
ESSAYS_DIR = ROOT / "essays"
POSTS_DIR = ESSAYS_DIR / "posts"
MANIFEST_PATH = ESSAYS_DIR / "manifest.json"


DISPLAY_NAMES = {
    "essay": "随笔",
    "daily": "日常",
    "study": "学习",
    "cs": "计算机",
    "cpp": "C++",
    "physics": "物理",
    "math": "数学",
    "mechanics": "力学",
    "notes": "笔记",
    "misc": "杂项",
}


DIR_PRIORITY = {
    "essay": 10,
    "daily": 20,
    "study": 30,
    "cs": 40,
    "cpp": 50,
    "physics": 60,
    "math": 70,
    "mechanics": 80,
    "notes": 90,
    "misc": 100,
}


def display_name(slug: str) -> str:
    if slug in DISPLAY_NAMES:
        return DISPLAY_NAMES[slug]

    return slug.replace("-", " ").replace("_", " ").title()


def parse_front_matter(text: str):
    meta = {}
    body = text

    lines = text.splitlines()

    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                front_matter_lines = lines[1:index]
                body = "\n".join(lines[index + 1:])

                for line in front_matter_lines:
                    if ":" not in line:
                        continue

                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if key:
                        meta[key] = value

                break

    return meta, body


def find_first_heading(markdown_body: str):
    for line in markdown_body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)

        if match:
            return match.group(1).strip()

    return None


def find_date_from_filename(filename: str):
    match = re.search(r"\d{4}-\d{2}-\d{2}", filename)

    if match:
        return match.group(0)

    return ""


def make_node(title: str):
    return {
        "title": title,
        "_children": {},
        "posts": []
    }


def insert_post(root_node, markdown_path: Path):
    relative_to_posts = markdown_path.relative_to(POSTS_DIR)
    directory_parts = relative_to_posts.parts[:-1]

    node = root_node

    for part in directory_parts:
        if part not in node["_children"]:
            node["_children"][part] = make_node(display_name(part))

        node = node["_children"][part]

    text = markdown_path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)

    title = (
        meta.get("title")
        or find_first_heading(body)
        or markdown_path.stem.replace("-", " ").replace("_", " ").title()
    )

    date = (
        meta.get("date")
        or find_date_from_filename(markdown_path.name)
    )

    path_from_essays = markdown_path.relative_to(ESSAYS_DIR).as_posix()

    post = {
        "title": title,
        "date": date,
        "path": path_from_essays
    }

    node["posts"].append(post)

    return post


def sort_directory_item(item):
    slug, node = item
    return (DIR_PRIORITY.get(slug, 999), node["title"])


def sort_post(post):
    return (post.get("date", ""), post.get("title", ""))


def convert_node(node):
    result = []

    for slug, child in sorted(node["_children"].items(), key=sort_directory_item):
        output = {
            "title": child["title"]
        }

        children = convert_node(child)
        posts = sorted(child["posts"], key=sort_post, reverse=True)

        if children:
            output["children"] = children

        if posts:
            output["posts"] = posts

        result.append(output)

    return result


def main():
    root_node = {
        "_children": {},
        "posts": []
    }

    all_posts = []

    if POSTS_DIR.exists():
        markdown_files = sorted(POSTS_DIR.rglob("*.md"))

        for markdown_path in markdown_files:
            if any(part.startswith(".") for part in markdown_path.parts):
                continue

            post = insert_post(root_node, markdown_path)
            all_posts.append(post)

    sections = convert_node(root_node)

    all_posts_sorted = sorted(all_posts, key=sort_post, reverse=True)
    default_post = all_posts_sorted[0]["path"] if all_posts_sorted else ""

    manifest = {
        "defaultPost": default_post,
        "sections": sections
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Generated {MANIFEST_PATH}")
    print(f"Found {len(all_posts)} markdown posts.")


if __name__ == "__main__":
    main()
