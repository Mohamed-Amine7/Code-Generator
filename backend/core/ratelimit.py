from slowapi import Limiter
from slowapi.util import get_remote_address

from core import config

# Derrière un reverse proxy, lance uvicorn avec --proxy-headers pour que l'IP soit correcte.
limiter = Limiter(key_func=get_remote_address, enabled=config.RATELIMIT_ENABLED)
