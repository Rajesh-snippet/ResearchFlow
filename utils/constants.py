"""
Shared constants for ResearchFlow.

config.py stays focused on LLM client setup (the Groq factory, the
structured() helper). Everything else that's a plain value - model
names, retry tuning, output limits - lives here so there's one obvious
place to look/add rather than it being split across files.
"""

# --- LLM ---
# llama-3.3-70b-versatile was deprecated by Groq on June 17, 2026.
# openai/gpt-oss-120b is Groq's recommended replacement.
DEFAULT_MODEL = "openai/gpt-oss-120b"

# --- Retry tuning (M3) ---
# Applied to structured-output calls (router/orchestrator/decide_images),
# which are the calls most likely to fail parsing/validation on a first try.
RETRY_MAX_ATTEMPTS = 3
RETRY_WAIT_MIN_SECONDS = 1
RETRY_WAIT_MAX_SECONDS = 8

# --- Image limits ---
MAX_IMAGES_PER_BLOG = 3
DEFAULT_IMAGE_SIZE = "1024x1024"

# --- Output paths ---
OUTPUTS_DIR = "outputs"
IMAGES_DIR = "images"

# --- Checkpointing (M5) ---
CHECKPOINT_DB_PATH = "researchflow_checkpoints.sqlite"

# Explicit allowlist for checkpoint (de)serialization (M5). Without this,
# LangGraph's default msgpack serializer allows reconstructing ANY Python
# type found in checkpoint data (only warning, not blocking) - a known
# security consideration if the checkpoint DB is ever compromised
# (see CVE-2026-28277). Restricting to exactly our own schema classes
# closes that off and also silences the "unregistered type" warning.
CHECKPOINT_ALLOWED_MSGPACK_MODULES = [
    ("schemas", "Task"),
    ("schemas", "Plan"),
    ("schemas", "EvidenceItem"),
    ("schemas", "RouterDecision"),
    ("schemas", "EvidencePack"),
    ("schemas", "ImageSpec"),
    ("schemas", "GlobalImagePlan"),
]

...
# Existing constants
LOG_LEVEL = "INFO"
DEFAULT_TIMEOUT = 30


# =============================================================================
# Rate Limiting
# =============================================================================

MAX_PARALLEL_LLM_CALLS = 2


# =============================================================================
# Retry Configuration
# =============================================================================

MAX_LLM_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
MAX_RETRY_DELAY = 30