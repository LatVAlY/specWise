import os

from dotenv import dotenv_values

config = {
    **dotenv_values(),
    **os.environ,
}
