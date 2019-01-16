import asyncio
import aiodns
import json
import os


async def main_loop(lookup, services):
    pass  # core logic here


def main():
    services = {} # yaml.safe_load('config.yml')

    loop = asyncio.get_event_loop()

    dns_resolver = aiodns.DNSResolver(loop=loop)

    lookup = lambda service : resolve_service(service, dns_resolver)
    
    loop.run_until_complete(main_loop(lookup, services))



if __name__ == '__main__':
    main()
