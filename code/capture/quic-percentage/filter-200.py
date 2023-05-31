#!/usr/bin/env python3

import sys
import os
import subprocess
import requests
import asyncio
import aiohttp
import time
import glob
import itertools
import json
import json
import re

H3_PATTERN = re.compile("h3-[TQ0-9]+=|quic=", re.IGNORECASE)


def http_status_bulk(infile, outpattern):

    async def get(url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url='https://'+url, timeout=5) as response:
                    altsvc = None
                    if 'alt-svc' in response.headers:
                        altsvc = response.headers['alt-svc']
                    elif 'Alt-Svc' in response.headers:
                        altsvc = response.headers['Alt-Svc']

                    if response.status == 200 and altsvc is not None and H3_PATTERN.match(altsvc):
                        return url
                            
        except Exception as e:
            pass
        return None
        

    async def parallel_process(urls):
        return await asyncio.gather(*[get(url) for url in urls])

    
    urls = []
    count = 0
    inc = 100
    with open(infile, "r") as f:
        for url in f:
            urls.append(url.strip())

            if len(urls) == inc:

                outfile = outpattern+str(count)+".txt"
                if os.path.isfile(outfile):
                    count += inc
                    urls = []
                    print("Skipping", outfile)
                    continue

                print("Processing", count, "-", count+inc, "->", outfile)
                valid_urls = asyncio.run(parallel_process(urls))
                valid_urls = [url for url in valid_urls if url is not None]
                
                with open(outfile, "w") as f2:
                    for u in valid_urls:
                        f2.write(u.strip()+"\n")

                count += inc
                urls = []


http_status_bulk('urls', 'dataset/urls-filtered-')