---
name: plenum-public-provider-boundary
description: Enforce read-only public provider boundary with redirect-refusing policy to keep clients within authorized destination and response policy
author: Plenum Engineering Specialist
---

## Objective

Keep a read-only public provider client within its authorized destination and response policy. Reject any unexpected final URL or non-200 status before reading response data to maintain authorization boundaries.

## Procedure

- Redirect-refusing behavior covers every default source without treating supervisory correction as autonomous success
- Retain existing request construction, response byte limit, and injected offline opener behavior
- Validate source integrity and test blobs at protected merge before any deployment

## Rules

- Unexpected final URL or non-200 status rejected immediately; do not read response data
- Authorization boundary is strict: no permission widening under any condition
- All behavioral tests must pass with all 1287 foundation tests verified before release