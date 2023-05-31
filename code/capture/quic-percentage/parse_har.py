"""
Parse Har files produced by firefox-quic-percentage.py
"""

from __future__ import annotations

from argparse import ArgumentParser
from json import loads
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Set, Union


RE_DOMAIN = re.compile("[^\.]+\.[^\.]+$")


class HarExtract(NamedTuple):
    """Data from Har file which interest us."""
    website: str
    domain: str
    rank: Union[int, float]
    requests_total: int
    requests_quic: int

    def percentage(self) -> float:
        """Compute percentage of QUIC requests."""
        if self.requests_total > 0:
            return 100.0 * self.requests_quic / self.requests_total
        return 0.0

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, HarExtract):
            raise ValueError("{other} is not a HarExtract.")

        percent = self.percentage()
        percent_other = other.percentage()

        # The equal case should never happen.
        if percent == percent_other:
            return self.rank < other.rank
        return percent > percent_other

    def __gt__(self, other: object) -> bool:
        return self.__gt__(other)

    def __le__(self, other) -> bool:
        return other.__ge__(self)

    def __lt__(self, other) -> bool:
        return other.__ge__(self)

    def __bool__(self) -> bool:
        return (self.website is not None) and bool(self.website)

    def __str__(self) -> str:
        return f"{self.website},{self.rank},{self.requests_total},{self.requests_quic}"


def build_ranking(rankfile: Path) -> Dict[str, int]:
    """Build the ranking of the websites"""
    ranks: Dict[str, int] = {}
    for rank_line in rankfile.read_text().split():
        rank_str, host = rank_line.split(",")
        ranks[host] = int(rank_str)
    return ranks


def parse_har(harfile: Path, ranks: Dict[str, int]) -> Optional[HarExtract]:
    """Parse a har file."""
    print(f"Processing {harfile}")
    har_content = harfile.read_text()
    if har_content == "":
        return None

    har_struct = loads(harfile.read_text())
    website = har_struct[0]

    if not website:
        return None

    requests: List[Dict[str, Any]] = har_struct[2]
    requests_quic = [r for r in requests if "altsvc" in [k.lower() for k in r.keys()]]

    domain_match = RE_DOMAIN.search(website)
    if domain_match is None:
        return None

    domain = domain_match.group()

    return HarExtract(
        website=website,
        domain=domain,
        rank=ranks.get(domain, math.inf),
        requests_total=len(requests),
        requests_quic=len(requests_quic)
    )


def parse_hars(dir_hars: Path, ranks: Dict[str, int]) -> List[HarExtract]:
    """Parse all Har files contained in a directory."""
    hars = list(filter(None, (parse_har(har_file, ranks) for har_file in dir_hars.glob("*.har"))))
    hars.sort(reverse=True)

    return hars


def filter_top_hars_by_domain(hars: List[HarExtract], top_n: Optional[int] = None) -> List[HarExtract]:
    domains: Set[str] = set()
    out: List[HarExtract] = []

    for har in hars:
        if har.domain in domains:
            continue
        domains.add(har.domain)
        out.append(har)

    if top_n is not None:
        return out[:top_n]
    else:
        return out


def write_csv(output: Path, hars: List[HarExtract]) -> None:
    """Write the extracted Har data in a CSV"""
    with output.open("w") as out_fd:
        out_fd.write('Website, Rank, "Request Total","Request QUIC"\n')
        out_fd.writelines(f"{har}\n" for har in hars)


def main(prog: str, args: List[str]) -> None:
    """Entry point of the program."""

    parser = ArgumentParser(prog)
    parser.add_argument(
        "urls",
        help="List of websites ordered by ranking",
        type=Path
    )
    parser.add_argument(
        "dataset",
        help="Directory containing the Har files",
        type=Path
    )
    parser.add_argument(
        "output",
        help="Output CSV file",
        type=Path
    )
    parser.add_argument(
        "-n",
        help="Take top n elements with an unique domain",
        type=int
    )
    namespace = parser.parse_args(args)

    urls: Path = namespace.urls
    urls = urls.resolve()
    if not urls.is_file():
        raise ValueError("Website ranking does not exist.")

    dataset: Path = namespace.dataset
    dataset.resolve()
    if not dataset.is_dir():
        raise ValueError("Dataset does not exist.")

    output: Path = namespace.output
    if output.exists():
        raise ValueError("Output file does already exist.")

    top_n: Optional[int] = namespace.n

    if top_n is not None and top_n <= 0:
        raise ValueError("Top n must be positive")

    # The real work starts here!
    ranks = build_ranking(urls)
    hars = parse_hars(dataset, ranks)
    if top_n:
        hars = filter_top_hars_by_domain(hars, top_n)
    write_csv(output, hars)


if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
