"""
政治特化CLIモジュール
政治予測システム専用のCLIインターフェースを提供
"""

from .political_app import PoliticalLainApp
from .political_commands import political_cli
from .political_interface import PoliticalInterface
from .integration_test import PoliticalSystemIntegrationTest, run_integration_test

__all__ = [
    'PoliticalLainApp',
    'political_cli',
    'PoliticalInterface',
    'PoliticalSystemIntegrationTest',
    'run_integration_test'
]