from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import logging
import subprocess
import sys

from scraper_paths import MODULE_LINKS_PATH, read_module_links


SCRIPT_DIR = Path(__file__).resolve().parent
LINK_GRABBER_SCRIPT = SCRIPT_DIR / "link_graber.py"
ONE_MODULE_SCRIPT = SCRIPT_DIR / "one-module.py"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("s_tec_scraper")


def parse_args():
    parser = argparse.ArgumentParser(description="S-TEC module orchestrator")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel module workers to run",
    )
    parser.add_argument(
        "--skip-collect",
        action="store_true",
        help="Skip refreshing module_links.txt and reuse the existing file",
    )
    return parser.parse_args()


def stream_command(command, label):
    logger.info("Starting %s: %s", label, " ".join(command))
    process = subprocess.Popen(
        command,
        cwd=SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    for line in process.stdout:
        logger.info("[%s] %s", label, line.rstrip())

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"{label} failed with exit code {return_code}")


def collect_module_links():
    stream_command([sys.executable, str(LINK_GRABBER_SCRIPT)], "collector")


def load_module_links():
    module_links = read_module_links()
    if not module_links:
        raise ValueError(f"No module links available in {MODULE_LINKS_PATH}")

    logger.info("Loaded %s module links from %s", len(module_links), MODULE_LINKS_PATH)
    return module_links


def launch_worker(module_link, worker_id):
    worker_label = f"worker-{worker_id}"
    command = [
        sys.executable,
        str(ONE_MODULE_SCRIPT),
        "--module-link",
        module_link,
        "--no-prompt",
    ]
    stream_command(command, worker_label)
    return module_link


def main():
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be at least 1")

    if not args.skip_collect:
        logger.info("Refreshing module list with %s", LINK_GRABBER_SCRIPT.name)
        collect_module_links()
    else:
        logger.info("Skipping collection and reusing %s", MODULE_LINKS_PATH)

    module_links = load_module_links()
    worker_count = min(args.workers, len(module_links))
    logger.info("Dispatching %s module(s) across %s worker(s)", len(module_links), worker_count)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(launch_worker, module_link, index + 1): module_link
            for index, module_link in enumerate(module_links)
        }

        for future in as_completed(futures):
            module_link = futures[future]
            future.result()
            logger.info("Completed module: %s", module_link)


if __name__ == "__main__":
    main()
