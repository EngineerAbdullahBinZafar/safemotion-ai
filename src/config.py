"""
SafeMotion AI — Configuration & SaaS Tiers
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = "SafeMotion AI & PhysShield Gateway"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/v1"
    AUTHOR: str = "Engineer Abdullah Bin Zafar"
    CONTACT: str = "abz.king.1.9.2003@gmail.com"
    
    # Defaults
    DEFAULT_ROBOT_RADIUS: float = 0.25
    DEFAULT_GAMMA: float = 1.8
    MAX_LINEAR_SPEED: float = 2.0
    MAX_ANGULAR_SPEED: float = 3.14

    # SaaS Tier Limits
    FREE_TIER_MONTHLY_QUOTA: int = 1_000
    PRO_TIER_MONTHLY_QUOTA: int = 100_000
    PRO_TIER_PRICE_USD: float = 39.0
    ENTERPRISE_TIER_PRICE_USD: float = 999.0


settings = Settings()
