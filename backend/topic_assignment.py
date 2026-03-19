"""Compatibility shim.

Use backend.story_assignment instead.
"""

from .story_assignment import run_story_assignment


if __name__ == "__main__":
    run_story_assignment()