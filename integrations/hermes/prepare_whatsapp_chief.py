"""Render the existing nine Plenum Hermes specialists as Chief-only profile routes.

Offline and secret-free. This config does NOT install Hermes, switch on a
WhatsApp adapter, create accounts, add Meta permissions or launch a host.
Uses official Hermes advanced-delegation profile_routes on a trusted host,
with explicit owner approval and a separate configured model required.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROSTER = Path(__file__).with_name("roster.json")
EXPECTED = frozenset({
    "chief", "research", "coding", "browser", "creative", "marketing",
    "operations", "simulation", "support", "verification", "business_advisor",
})
MAX_CONCURRENT = 2


def read_roles(path=ROSTER):
    """Return the canonical roster; fail on drift or unreviewed extra roles."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    roles = data.get("roles")
    if (data.get("schema") != "plenum-hermes-profile-roster-v1"
            or not isinstance(roles, list) or len(roles) != 11
            or any(not isinstance(r, dict) for r in roles)):
        raise ValueError("Invalid canonical Hermes roster")
    by_name = {role.get("name"): role for role in roles}
    if len(by_name) != 11 or set(by_name) != EXPECTED:
        raise ValueError("Expected one Chief, nine original specialists, and one Business Advisor")
    if data.get("defaults", {}).get("cost_usd") != 0 or data.get("defaults", {}).get("private_app_access") is not False:
        raise PermissionError("The existing zero-spend and no-private-account policy must remain")
    for name, role in by_name.items():
        if (not isinstance(role.get("scope"), str) or not 5 <= len(role["scope"]) <= 500
                or "\n" in role["scope"] or "\r" in role["scope"]):
            raise ValueError("Unreviewed or multiline specialist scope")
    return by_name


def render_chief_routes(roles=None):
    """Use official advanced-delegation names and only already-approved roles."""
    roles = read_roles() if roles is None else roles
    if set(roles) != EXPECTED:
        raise ValueError("Original specialists and the Business Advisor are required")
    lines = [
        "# OFFLINE EXAMPLE. Requires Hermes >=0.22.5 and its official",
        "# advanced-delegation plugin enabled in the Chief profile.",
        "# Add this block to the Chief's private config.yaml only after",
        "# the specialist profiles and their approved local model exist.",
        "# It does NOT activate a WhatsApp number, group or network service.",
        "delegation:",
        "  backend: profile_routes",
        "  max_concurrent_children: 2",
        "  max_spawn_depth: 1",
        "  orchestrator_enabled: false",
        "  backends:",
        "    profile_routes:",
        "      profiles:",
    ]
    for name in sorted(EXPECTED - {"chief"}):
        lines.append(f"        - name: {name}")
        lines.append("          description: " + json.dumps(roles[name]["scope"], ensure_ascii=True))
    return "\n".join(lines) + "\n"


def safe_write(path, content):
    """Owner request only, cannot overwrite existing private Hermes configuration."""
    target = Path(path).expanduser()
    if target.is_symlink() or target.exists():
        raise FileExistsError("Will not overwrite any existing Hermes configuration")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise ValueError("Destination parent must be an existing trusted directory")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None,
                        help="Create a new 0600 YAML snippet in an existing owner-controlled folder")
    args = parser.parse_args(argv)
    rendered = render_chief_routes()
    if args.output is None:
        print(json.dumps({
            "status": "OFFLINE_CHIEF_CONFIG_READY",
            "specialist_count": 10,
            "roles": sorted(EXPECTED - {"chief"}),
            "max_concurrent_children": MAX_CONCURRENT,
            "whatsapp_group_connected": False,
            "hermes_gateway_running": False,
            "model_running": False,
            "paid_host_created": False,
            "requires": [
                "owner-controlled Hermes 0.22.5+ host",
                "official advanced-delegation plugin",
                "ten separately provisioned permitted profiles with model",
                "authorized dedicated WhatsApp number and founder/group allowlists",
            ],
        }, indent=2))
    else:
        safe_write(args.output, rendered)
        print("CREATED_PRIVATE_0600_CHIEF_CONFIG_SNIPPET (not installed or enabled)")


if __name__ == "__main__":
    main()
