"""
政治データ管理モジュール  
政治家・政党・選挙・世論調査データの管理を提供
"""

from .political_entities import PoliticalEntityManager
from .election_data import ElectionDataManager
from .poll_data import PollDataManager
from .political_dictionary import PoliticalDictionary
from .political_database import PoliticalDatabaseManager

__all__ = [
    'PoliticalEntityManager',
    'ElectionDataManager',
    'PollDataManager', 
    'PoliticalDictionary',
    'PoliticalDatabaseManager'
]