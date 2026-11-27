# Checkpoint maintainer visual guide

A repository-development aid for the original Chief checkpoint implementation, not a new production service or marketing render. The verified `save_checkpoint` change in #995 validates the issue identifier before creating a directory. It serializes bounded JSON, creates an exclusive temporary file, flushes and fsyncs the file, then replaces the previous checkpoint. The original #997 repair promoted in #999 converts excessive JSON nesting into a rejected checkpoint (ValueError). An invalid checkpoint is not permission to replay a reserved operation.

The static scene uses blue (original checkpoint), amber (temporary write), and green (replacement) blocks in that order. The motion guide explains the corresponding write path and the rejection branch. Its labels are conceptual, not a record of a live mission. The original renderer and offline network boundary are reused. See [the source](../../src/plenum_ai/mission_checkpoint.py) for precise behavior. Read source rather than inferring crash guarantees from this illustration; the present source fsyncs the temporary file, not the directory.

Render evidence must include exact inputs, actual image/video, SHA-256, and separate inspection before claiming useful output. No private data or external publication; no owner-local runtime claim. The original fixture qualification evidence is unchanged.
