import asyncio
import aiodns
import aiohttp
import json
import os
import dnslookup
import time
import random
import yaml
from functools import reduce

async def fetch_json(url, session):
    async with session.get(url) as response:
        return await response.json()


def version_num_from_resp(json_data):
    return f"v{json_data.get('version')}"


async def process_domain(domain_name, endpoint, lookup, session):
    domains = await lookup(domain_name)
    tasks = []
    for d in domains:
        tasks.append(fetch_json(f'{d}/{endpoint}', session))

    results = await asyncio.gather(*tasks)

    versions = [version_num_from_resp(r) for r in results]

    return versions


def compress_service_versions(acc, cur):
    acc[cur] = 1 if acc.get(cur) is None else acc[cur] + 1
    return acc


async def main_loop(lookup, session, services):
    stop = False
    checking_services = [*services]
    while not stop:
        tasks = []
        for service in checking_services:
            tasks.append(process_domain(service['url'], service['version_endpoint'], lookup, session))

        results = await asyncio.gather(*tasks)

        for idx, service in enumerate(checking_services):
            service['current_versions'] = results[idx]

        for service in checking_services:
            compressed_services = reduce(compress_service_versions, service['current_versions'], {})
            print(f"{service['name']} -> {[f'{k} x {v} nodes' for k, v in compressed_services.items()]}")
            if compressed_services.get(service['target_version']) == service['expected_nodes']:
                if service.get('status') == 'good':
                    service['done'] = True
                else:
                    service['status'] = 'good'

        if len([1 for s in checking_services if s.get('done')]) == 0:
            stop = True
        else:
            await asyncio.sleep(3)



def main():
    async def shutdown():
        await session.close()

    with open('config.yml', 'r') as fh:
        config = yaml.safe_load(fh)

    services = config['services']
    for s in services:
        s['url'] = s['url'].format(env=config['env'])
    
    loop = asyncio.get_event_loop()

    dns_resolver = aiodns.DNSResolver(loop=loop)

    async def lookup(service):
        return await dnslookup.resolve_service(service, dns_resolver)

    session = aiohttp.ClientSession()
    
    try:
        loop.run_until_complete(main_loop(lookup, session, services))
#    except:
#        print("exiting")
    finally:
        loop.run_until_complete(shutdown())


if __name__ == '__main__':
    main()
