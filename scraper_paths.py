from pathlib import Path


MODULE_LINKS_PATH = Path(__file__).resolve().with_name("module_links.txt")


def read_module_links():
    if not MODULE_LINKS_PATH.exists():
        return []

    with MODULE_LINKS_PATH.open("r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def write_module_links(module_links):
    with MODULE_LINKS_PATH.open("w", encoding="utf-8") as file:
        for module_link in module_links:
            file.write(f"{module_link}\n")
