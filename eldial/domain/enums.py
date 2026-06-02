from enum import Enum


class UnitSystem(str, Enum):
  SI = "si"
  CGS = "cgs"
  CUSTOM = "custom"
