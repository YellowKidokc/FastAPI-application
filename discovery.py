from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from config import HOSTS, PORTS, PREFERRED_ROUTE_ORDER, REQUEST_TIMEOUT_SECONDS, SERVICE_PORTS

Topology = dict[str, dict[str, Any]]
_DISCOVERY_CACHE: Topology = {}
_DISCOVERY_TS = 0.0
_DISCOVERY_TTL_SECONDS = 30.0


async def _probe(host: str, port: int) -> bool:
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(f"http://{host}:{port}/health")
        return response.status_code < 500
    except (httpx.HTTPError, OSError, TimeoutError):
        return False


async def scan_ports(host: str | None, ports: list[int] | tuple[int, ...] = SERVICE_PORTS) -> dict[int, bool]:
    """Check which POF 2828 ports respond on a host."""
    if not host:
        return {port: False for port in ports}
    results = await asyncio.gather(*(_probe(host, port) for port in ports), return_exceptions=True)
    return {port: bool(result) if not isinstance(result, Exception) else False for port, result in zip(ports, results)}


async def discover_topology() -> Topology:
    """Return each known machine, route, and service availability."""
    global _DISCOVERY_CACHE, _DISCOVERY_TS
    now = time.monotonic()
    if _DISCOVERY_CACHE and now - _DISCOVERY_TS < _DISCOVERY_TTL_SECONDS:
        return _DISCOVERY_CACHE

    topology: Topology = {}
    tasks: dict[tuple[str, str], asyncio.Task[dict[int, bool]]] = {}
    for machine, routes in HOSTS.items():
        topology[machine] = {"routes": routes, "services": {}}
        for route_name, host in routes.items():
            tasks[(machine, route_name)] = asyncio.create_task(scan_ports(host, SERVICE_PORTS))

    for (machine, route_name), task in tasks.items():
        host = HOSTS[machine].get(route_name)
        ports = await task
        topology[machine]["services"][route_name] = {
            str(port): {"online": online, "host": host, **PORTS[port]} for port, online in ports.items()
        }

    _DISCOVERY_CACHE = topology
    _DISCOVERY_TS = now
    return topology


async def best_route(service_port: int) -> str | None:
    """Return the preferred reachable IP for a service, favoring 10GbE direct routes."""
    topology = await discover_topology()
    for route_name in PREFERRED_ROUTE_ORDER:
        for machine in ("nas", "desktop", "laptop"):
            route_services = topology.get(machine, {}).get("services", {}).get(route_name, {})
            service = route_services.get(str(service_port))
            if service and service["online"] and service.get("host"):
                return service["host"]
    return None


async def should_proxy_to_laptop(service_port: int) -> str | None:
    laptop_lan = HOSTS.get("laptop", {}).get("lan")
    if not laptop_lan:
        return None
    ports = await scan_ports(laptop_lan, (service_port,))
    return laptop_lan if ports.get(service_port) else None
