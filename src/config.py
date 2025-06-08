from pathlib import Path

# The root directory of the entire project
PROJECT_ROOT = Path(__file__).parent

# Define paths for all our specialized directories relative to the project root
ACL_DIR = PROJECT_ROOT / "acl"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = PROJECT_ROOT / "keys"
MODELS_DIR = PROJECT_ROOT / "models"
CORE_DIR = PROJECT_ROOT / "core"
UTILS_DIR = PROJECT_ROOT / "utils"

# Define specific file paths
DB_PATH = DATA_DIR / "spanning_tree.db"
PRIVATE_KEY_PATH = KEYS_DIR / "id_ed25519"
PUBLIC_KEY_PATH = KEYS_DIR / "id_ed25519.pub"
