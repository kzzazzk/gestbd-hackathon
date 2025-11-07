import pandas as pd
import pyalex
from pyalex import Works, Authors, Sources, Institutions, Topics, Publishers, Funders, config

# Configuracion de busqueda
config.max_retries = 0
config.retry_backoff_factor = 0.1
config.retry_http_codes = [429, 500, 503]

works = Works().count()
print(works)