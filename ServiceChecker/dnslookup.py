import aiodns
import asyncio
import sys

from collections import namedtuple
from typing import List
from aiodns.error import DNSError
from urllib.parse import urlparse

Service = namedtuple("Service", ['host', 'port'])


async def _lookup(domain, resolver, lookup_type='SRV'):
    try:
        result = await resolver.query(domain, lookup_type)
    except DNSError as e:
        if e.args[0] == 4:
            return LookupStatus(success=False, reason=f"Cannot find domain: {domain}")
        else:
            return LookupStatus(success=False, reason=f"Unexpected DNS error: {e}")
    except Exception as e:
        return LookupStatus(success=False, reason=f"Unexpected error:{sys.exc_info()[0]} -> {e}")
    else:
        return LookupStatus(success=True, services=[Service(x.host, x.port) for x in result])


async def resolve_service(service, dns_resolver):
    """
    resolve_service is the "public" interface to looking up services. it splits the domain, does the srv lookup,
    then generates the service domain name for the looked up service. If the lookup fails for some reason, then
    the a blank service is returned (i.e. "")
    """

    prefix, selected_domain = split_domain(service)

    lookup_result = await _lookup(selected_domain, dns_resolver)

    if lookup_result.success:
        selected_domain = [f"{prefix}{svc.host}:{svc.port}" for svc in lookup_result.services]
    else:
        selected_domain = []

    return selected_domain


def split_domain(addr):
    parsed = urlparse(addr)

    if parsed.scheme != '':
        proto = f"{parsed.scheme}://"
        domain = parsed.hostname
    else:
        # when no scheme is supplied, domain is in the path (see RFC 1808)
        idx = parsed.path.find('/')
        domain = parsed.path if idx == -1 else parsed.path[:idx]
        proto = ""

    return proto, domain


class LookupStatus(object):
    def __init__(self, success=None, reason=None, services=None):
        self.success:bool = success
        self.reason:str = reason
        self.services:List[Service] = services
