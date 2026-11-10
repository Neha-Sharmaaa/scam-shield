"""Fixed agent script (no LLM). Devanagari text is sent to Timbre (hi-IN);
the Roman line is shown on screen.

Guard-rails: the agent never confirms the parent's details, never repeats
anything the caller says, never hints at the code word, and never accuses.
"""

# Gena's lines and the parent-message templates for every language live in app/lang.py.
BASE_STEPS = ["name", "org", "purpose"]
