"""
SafeMotion AI & PhysShield Gateway Package
Author: Engineer Abdullah Bin Zafar
"""

from .cbf_core import CBFSafetyFilter

try:
    from .models import ControlInput, Obstacle, RobotState, SafetyFilterRequest, SafetyFilterResponse
    __all__ = [
        "CBFSafetyFilter",
        "RobotState",
        "ControlInput",
        "Obstacle",
        "SafetyFilterRequest",
        "SafetyFilterResponse",
    ]
except ImportError:
    # Pure Python zero-dependency mode (for demo.py and embedded targets)
    __all__ = ["CBFSafetyFilter"]
