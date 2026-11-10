"""Hermes-native restricted public workforce tools. Install in Chief profile only."""
from __future__ import annotations

import json
import os

from plenum_ai.hermes_issue_bridge import create_public_assignment, read_public_assignment


def register(ctx):
    assign = {
        "name": "plenum_assign_public_task",
        "description": "Queue one PUBLIC nonconfidential founder instruction for an original Plenum research, code-starter, known-model science, or creative worker. An issue is created but NOT completed by this call. Never submit private records, account actions, funds, customer information or IP.",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": ["public_research", "public_program",
                             "public_science", "public_creative"],
                },
                "objective": {
                    "type": "string", "minLength": 20, "maxLength": 120,
                    "description": "Explicitly PUBLIC and nonconfidential bounded objective",
                },
            },
            "required": ["kind", "objective"],
        },
    }

    def handle_assign(params, **kwargs):
        del kwargs
        try:
            result = create_public_assignment(
                params.get("kind"), params.get("objective"),
                token=os.environ.get("PLENUM_GITHUB_PUBLIC_ISSUES_TOKEN", ""),
            )
            return json.dumps(result)
        except (ValueError, PermissionError, RuntimeError, OSError) as exc:
            # Do not echo API error bodies, prompts or private credentials.
            return json.dumps({"state": "BLOCKED", "reason": type(exc).__name__,
                               "external_assignment_verified": False})

    ctx.register_tool(
        name="plenum_assign_public_task", toolset="plenum_public_workforce",
        schema=assign, handler=handle_assign,
    )

    status = {
        "name": "plenum_read_public_task_status",
        "description": "Read only the validated outcome status left by GitHub Actions on a previously founder-authorized PUBLIC Plenum Issue. Does not expose the source Issue content.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "minimum": 1},
            },
            "required": ["issue_number"],
        },
    }

    def handle_read(params, **kwargs):
        del kwargs
        try:
            value = read_public_assignment(
                params.get("issue_number"),
                token=os.environ.get("PLENUM_GITHUB_PUBLIC_ISSUES_TOKEN", ""),
            )
            return json.dumps(value)
        except (ValueError, PermissionError, RuntimeError, OSError) as exc:
            return json.dumps({"state": "BLOCKED", "reason": type(exc).__name__,
                               "private_content_exposed": False})

    ctx.register_tool(
        name="plenum_read_public_task_status", toolset="plenum_public_workforce",
        schema=status, handler=handle_read,
    )
