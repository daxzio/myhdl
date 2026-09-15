"""Shared constants for cosim bench tests."""

import random
from random import randrange

random.seed(2)

ACTIVE_LOW, INACTIVE_HIGH = 0, 1
VALS = [randrange(2) for _ in range(1000)]
