import os
from dotenv import load_dotenv
from typing import Optional, Union
from dataclasses import dataclass


load_dotenv()


@dataclass
class Config:
    document_size: int = 1000

def env_var(name: str) -> Optional[Union[str,int]]:
    # todo: can os.environ have any other types ? w.e
    try:
        return os.environ[name]
    except KeyError:
        return None

CONFIG = Config()
for name, default_value in vars(CONFIG).items():
    CONFIG.__setattr__(
        name,
        env_var(name) or default_value
    )

