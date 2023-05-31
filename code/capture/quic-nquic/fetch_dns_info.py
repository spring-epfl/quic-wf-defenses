from __future__ import annotations

from argparse import ArgumentParser
from json import dumps as json_dumps, loads as json_loads
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

from dns.resolver import Resolver

NAMESERVERS = ["1.1.1.1"]

def setup_logger():
    """Setup the logger."""
    logger = logging.getLogger("Fetch DNS info")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


LOGGER = setup_logger()


class HarInfo:
    def __init__(self, website: str, hosts: List[str]) -> None:
        self.website = website
        self.hosts: Dict[str, List[str]] = {host: [] for host in hosts}

    @classmethod
    def parse_har(cls, har_file: Path) -> Optional[HarInfo]:
        content = json_loads(har_file.read_text())
        if not content:
            return None

        website = content[0]

        if website is None:
            return None

        links: List[Dict[str, Any]] = content[2]

        hosts: List[str] = [link["host"] for link in links]

        return cls(website, hosts)


    def fetch_addrinfo(self, resolver: Resolver) -> None:
        for host in self.hosts.keys():
            try:
                ips = [rdata.address for rdata in resolver.resolve(host)]
                self.hosts[host] = ips
                LOGGER.info("Fetched DNS info for %s", host)
            except:
                LOGGER.warning("Failed to retrieve info for %s", host)


def retrieve_all_addrinfo(dataset_dir: Path, output_file: Path) -> None:
    har_files = dataset_dir.glob("*.har")

    hars: List[HarInfo] = list(
        filter(lambda x: x is not None,
        (HarInfo.parse_har(har_file) for har_file in har_files)) # type: ignore
    )

    resolver = Resolver()
    resolver.nameservers = NAMESERVERS

    for har in hars:
        har.fetch_addrinfo(resolver)

    json_struct = {har.website: har.hosts for har in hars}
    output_file.write_text(json_dumps(json_struct))


def main(program: str, args: List[str]):
    parser = ArgumentParser(program)

    parser.add_argument(
        "dataset",
        type=Path
    )

    parser.add_argument(
        "output",
        type=Path
    )

    namespace = parser.parse_args(args)

    dataset: Path = namespace.dataset
    if not dataset.is_dir():
        raise Exception(f"{dataset} does not exists!")

    output: Path = namespace.output
    if output.exists():
        raise Exception(f"{output} already exists!")

    retrieve_all_addrinfo(dataset, output)


if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
