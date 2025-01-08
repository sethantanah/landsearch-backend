# cache.py
from collections import deque

# Global cache with a fixed size
DOCUMENT_CACHE_SIZE = 1000
document_data_cache = deque(maxlen=DOCUMENT_CACHE_SIZE)
unedited_document_data_cache = deque(maxlen=100)
