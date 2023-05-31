import logging
from pathlib import Path
import re
import sys
from typing import Iterable, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup, SoupStrainer


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)


class InvalidETLD(ValueError):
    """ETLD is not parsable"""


class InvalidResponseStatus(ValueError):
    """The response is not a 200"""


LINKS_PER_WEBSITES = 35
RE_ETLD = re.compile("[^\.]+\.[^\.]+$")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
}


class Link:
    def __init__(self, host: str, path: str):
        if path.startswith("//"):
            url = f"https:{path}"
        elif path.startswith("/"):
            url = f"https://{host}{path}"
        else:
            url = path

        self.url = url
        self.redirections: List[str] = []

    def fetch_link(self) -> Tuple[bytes, Optional[str]]:

        response = requests.get(self.url, headers=HEADERS)

        if response.status_code != 200:
            logging.warning("Link returned a non-200 status code %d", response.status_code)
            raise InvalidResponseStatus()

        for redirect in response.history:
            self.redirections.append(redirect.url)

        return response.content, response.encoding

    def __hash__(self) -> int:
        return hash(self.url)

    def __str__(self) -> str:
        return self.redirections[-1] if self.redirections else self.url


class Website:
    MAX_LINKS = 35

    def __init__(self, host: str):
        self.host = host
        self.links: List[Link] = []

        etld_match = RE_ETLD.search(host)
        if etld_match is None:
            logging.warning("Invalid ETLD: %s", host)
            raise InvalidETLD()
        etld = etld_match.group(0)
        self.re_href = re.compile(f"^http://{etld}/|^https://{etld}/|^http://[^\.]+\.{etld}/|^https://[^\.]+\.{etld}/|^/")


    def parse_links(self, content: bytes, encoding: Optional[str]) -> Iterable[Link]:
        soup = BeautifulSoup(content, "html.parser", from_encoding=encoding)
        return (Link(self.host, link["href"]) for link in soup.find_all('a', attrs={'href': self.re_href}) if link is not None)


    def fetch_links(self) -> None:
        response = requests.get(f"https://{self.host}", headers=HEADERS)
        if response.status_code != 200:
            logging.warning("Host returned a non-200 status code %d", response.status_code)
            raise InvalidResponseStatus()

        ignore: Set[str] = {"/"}

        for link in self.parse_links(response.content, response.encoding):
            if link.url in ignore:
                continue

            ignore.add(link.url)
            self.links.append(link)

            if len(self.links) >= Website.MAX_LINKS:
                return

        for link in self.links:
            try:
                content, encoding = link.fetch_link()
            except:
                logging.warning("Failed to fetch root level link %s", str(link))
                continue

            for link in self.parse_links(content, encoding):
                if link.url in ignore:
                    continue

                ignore.add(link.url)

                try:
                    link.fetch_link()
                except:
                    logging.warning("Failed to fetch 1st level link %s", str(link))
                    continue

                self.links.append(link)

                if len(self.links) >= Website.MAX_LINKS:
                    return

    def __str__(self) -> str:
        links = [f"{idx + 1} {link}" for idx, link in enumerate(self.links)]
        return "\n".join(links)



def help_usage() -> None:
    sys.stderr.write(f"{sys.argv[0]} <WEBSITE LIST FILE> <OUTPUT DIR>")
    sys.stderr.flush()


def main():
    if len(sys.argv) != 3:
        help_usage()
        sys.exit(1)

    host_list_file = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2])

    if not host_list_file.is_file():
        logging.error("Host list %s does not exists.", host_list_file)
        help_usage()
        sys.exit(1)

    if output_dir.exists():
        output_dir = output_dir.resolve()
    else:
        output_dir.mkdir()

    if not output_dir.is_dir():
        logging.error("Output directory %s is not a directory.", output_dir)
        help_usage()
        sys.exit(1)

    host_list = host_list_file.read_text().split()

    for idx, host in enumerate(host_list):
        logging.info("======================")
        logging.info("Processing %d/%d : %s", idx+1, len(host_list), host)

        links_list_file = output_dir / f"{idx}_{host}"

        try:
            website = Website(host)
            website.fetch_links()
        except:
            logging.exception("Skip website.")
            continue

        links_list_file.write_text(str(website))


if __name__ == "__main__":
    main()

