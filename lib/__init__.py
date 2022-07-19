from .SSBConfig import SSBConfig
from .SSBArgs import SSBArgs
from .Backup    import Backup
import logging, sys

logging.basicConfig(stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s (%(levelname)s) - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%SZ')
log = logging.getLogger('ssb')
