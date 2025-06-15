#!/usr/bin/env python3
"""
政治家情報バッチ処理システム
"""
import logging
import json
import time
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .bing_scraper import BingScraper
from .url_scraper import URLScraper
from .llm_politician_extractor import LLMPoliticianExtractor
from ..llm.client import LLMClient
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class BatchPoliticianProcessor:
    """政治家情報バッチ処理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        
        # 各コンポーネントを初期化
        self.bing_scraper = BingScraper(config_manager)
        self.url_scraper = URLScraper()
        self.llm_client = LLMClient(config_manager)
        self.llm_extractor = LLMPoliticianExtractor(self.llm_client)
        
        # データベースパス
        self.db_path = Path("data/politician_database.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        # バッチ処理設定
        self.max_urls_per_politician = 3  # 各政治家あたりの最大URL数
        self.batch_delay = 30  # バッチ間の待機時間（秒）
        self.error_retry_count = 2  # エラー時のリトライ回数
        
        # データベース初期化
        self._init_database()
        
        logger.info("バッチ政治家処理システムを初期化")
    
    def process_politician_list(self, politician_names: List[str], batch_size: int = 5) -> Dict[str, Any]:
        """
        政治家リストをバッチ処理
        
        Args:
            politician_names: 政治家名のリスト
            batch_size: バッチサイズ
            
        Returns:
            処理結果サマリー
        """
        try:
            total_count = len(politician_names)
            processed_count = 0
            success_count = 0
            error_count = 0
            
            start_time = time.time()
            
            logger.info(f"バッチ処理開始: {total_count}名の政治家を処理")
            
            # バッチごとに処理
            for i in range(0, total_count, batch_size):
                batch = politician_names[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_count + batch_size - 1) // batch_size
                
                logger.info(f"バッチ {batch_num}/{total_batches} 開始: {len(batch)}名")
                
                # バッチ内の各政治家を処理
                for j, politician_name in enumerate(batch, 1):
                    try:
                        logger.info(f"処理中 [{batch_num}-{j}]: {politician_name}")
                        
                        # 既にデータベースに存在するかチェック
                        if self._politician_exists(politician_name):
                            logger.info(f"スキップ（既存）: {politician_name}")
                            processed_count += 1
                            continue
                        
                        # 政治家情報を処理
                        result = self._process_single_politician(politician_name)
                        
                        if result['success']:
                            success_count += 1
                            logger.info(f"成功: {politician_name}")
                        else:
                            error_count += 1
                            logger.warning(f"失敗: {politician_name} - {result.get('error', 'Unknown error')}")
                        
                        processed_count += 1
                        
                        # 進捗表示
                        progress = (processed_count / total_count) * 100
                        elapsed = time.time() - start_time
                        estimated_total = elapsed * total_count / processed_count if processed_count > 0 else 0
                        remaining = estimated_total - elapsed
                        
                        print(f"進捗: {processed_count}/{total_count} ({progress:.1f}%) - "
                              f"成功: {success_count}, 失敗: {error_count} - "
                              f"残り時間: {remaining/60:.1f}分")
                        
                    except Exception as e:
                        error_count += 1
                        processed_count += 1
                        logger.error(f"処理エラー: {politician_name} - {str(e)}")
                
                # バッチ間の待機（最後のバッチ以外）
                if i + batch_size < total_count:
                    logger.info(f"バッチ間待機: {self.batch_delay}秒")
                    time.sleep(self.batch_delay)
            
            # 処理結果をまとめ
            end_time = time.time()
            total_time = end_time - start_time
            
            summary = {
                'total_politicians': total_count,
                'processed_count': processed_count,
                'success_count': success_count,
                'error_count': error_count,
                'success_rate': (success_count / processed_count * 100) if processed_count > 0 else 0,
                'total_time_seconds': total_time,
                'average_time_per_politician': total_time / processed_count if processed_count > 0 else 0,
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat()
            }
            
            logger.info(f"バッチ処理完了: {success_count}/{total_count} 成功 ({summary['success_rate']:.1f}%)")
            return summary
            
        except Exception as e:
            logger.error(f"バッチ処理エラー: {str(e)}")
            raise
    
    def _process_single_politician(self, politician_name: str) -> Dict[str, Any]:
        """単一政治家の情報を処理"""
        try:
            # 1. Bing検索
            search_results = self.bing_scraper.search(
                politician_name, 
                max_results=self.max_urls_per_politician
            )
            
            if not search_results:
                return {
                    'success': False,
                    'error': '検索結果なし',
                    'politician_name': politician_name
                }
            
            # 2. URL スクレイピング
            urls = [result['url'] for result in search_results]
            scraped_contents = self.url_scraper.scrape_multiple_urls(urls)
            
            if not scraped_contents:
                return {
                    'success': False,
                    'error': 'スクレイピング失敗',
                    'politician_name': politician_name
                }
            
            # 3. LLM情報抽出
            extraction_results = []
            for content in scraped_contents:
                try:
                    extracted = self.llm_extractor.extract_politician_info(content)
                    extraction_results.append(extracted)
                except Exception as e:
                    logger.warning(f"LLM抽出エラー: {content.get('url', 'Unknown')} - {str(e)}")
                    continue
            
            if not extraction_results:
                return {
                    'success': False,
                    'error': 'LLM抽出失敗',
                    'politician_name': politician_name
                }
            
            # 4. LLM情報統合
            integrated_info = self.llm_extractor.integrate_multiple_extractions(extraction_results)
            
            if 'error' in integrated_info or not integrated_info.get('name'):
                return {
                    'success': False,
                    'error': 'LLM統合失敗',
                    'politician_name': politician_name
                }
            
            # 5. データベースに保存
            self._save_politician_data(
                politician_name,
                search_results,
                scraped_contents,
                extraction_results,
                integrated_info
            )
            
            return {
                'success': True,
                'politician_name': politician_name,
                'extracted_name': integrated_info.get('name'),
                'confidence_level': integrated_info.get('confidence_level', 'unknown'),
                'source_count': len(scraped_contents)
            }
            
        except Exception as e:
            logger.error(f"政治家処理エラー: {politician_name} - {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'politician_name': politician_name
            }
    
    def _init_database(self):
        """データベースを初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 政治家マスターテーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS politicians (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        search_name TEXT NOT NULL,
                        extracted_name TEXT,
                        reading TEXT,
                        age INTEGER,
                        birth_date TEXT,
                        birth_place TEXT,
                        current_party TEXT,
                        constituency TEXT,
                        election_type TEXT,
                        family TEXT,
                        confidence_level TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(search_name)
                    )
                """)
                
                # 政党履歴テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS party_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        politician_id INTEGER,
                        party_name TEXT NOT NULL,
                        order_index INTEGER,
                        FOREIGN KEY (politician_id) REFERENCES politicians(id)
                    )
                """)
                
                # 役職履歴テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        politician_id INTEGER,
                        position_name TEXT NOT NULL,
                        order_index INTEGER,
                        FOREIGN KEY (politician_id) REFERENCES politicians(id)
                    )
                """)
                
                # 学歴テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS education (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        politician_id INTEGER,
                        school_name TEXT NOT NULL,
                        order_index INTEGER,
                        FOREIGN KEY (politician_id) REFERENCES politicians(id)
                    )
                """)
                
                # 経歴テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS career (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        politician_id INTEGER,
                        career_item TEXT NOT NULL,
                        order_index INTEGER,
                        FOREIGN KEY (politician_id) REFERENCES politicians(id)
                    )
                """)
                
                # 情報源テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        politician_id INTEGER,
                        source_url TEXT NOT NULL,
                        source_title TEXT,
                        source_domain TEXT,
                        confidence_score REAL,
                        scraped_at TEXT,
                        FOREIGN KEY (politician_id) REFERENCES politicians(id)
                    )
                """)
                
                conn.commit()
                logger.info("データベーステーブル初期化完了")
                
        except Exception as e:
            logger.error(f"データベース初期化エラー: {str(e)}")
            raise
    
    def _politician_exists(self, politician_name: str) -> bool:
        """政治家がデータベースに存在するかチェック"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM politicians WHERE search_name = ?",
                    (politician_name,)
                )
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"存在チェックエラー: {str(e)}")
            return False
    
    def _save_politician_data(self, search_name: str, search_results: List[Dict], 
                            scraped_contents: List[Dict], extraction_results: List[Dict],
                            integrated_info: Dict[str, Any]):
        """政治家データをデータベースに保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                # メイン情報を挿入
                cursor.execute("""
                    INSERT OR REPLACE INTO politicians (
                        search_name, extracted_name, reading, age, birth_date, birth_place,
                        current_party, constituency, election_type, family, confidence_level,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    search_name,
                    integrated_info.get('name', ''),
                    integrated_info.get('reading', ''),
                    integrated_info.get('age'),
                    integrated_info.get('birth_date', ''),
                    integrated_info.get('birth_place', ''),
                    integrated_info.get('current_party', ''),
                    integrated_info.get('constituency', ''),
                    integrated_info.get('election_type', ''),
                    integrated_info.get('family', ''),
                    integrated_info.get('confidence_level', ''),
                    now, now
                ))
                
                politician_id = cursor.lastrowid
                
                # 関連データを削除（更新の場合）
                for table in ['party_history', 'positions', 'education', 'career', 'sources']:
                    cursor.execute(f"DELETE FROM {table} WHERE politician_id = ?", (politician_id,))
                
                # 政党履歴を挿入
                for i, party in enumerate(integrated_info.get('party_history', [])):
                    cursor.execute(
                        "INSERT INTO party_history (politician_id, party_name, order_index) VALUES (?, ?, ?)",
                        (politician_id, party, i)
                    )
                
                # 役職を挿入
                for i, position in enumerate(integrated_info.get('positions', [])):
                    cursor.execute(
                        "INSERT INTO positions (politician_id, position_name, order_index) VALUES (?, ?, ?)",
                        (politician_id, position, i)
                    )
                
                # 学歴を挿入
                for i, school in enumerate(integrated_info.get('education', [])):
                    cursor.execute(
                        "INSERT INTO education (politician_id, school_name, order_index) VALUES (?, ?, ?)",
                        (politician_id, school, i)
                    )
                
                # 経歴を挿入
                for i, career_item in enumerate(integrated_info.get('career', [])):
                    cursor.execute(
                        "INSERT INTO career (politician_id, career_item, order_index) VALUES (?, ?, ?)",
                        (politician_id, career_item, i)
                    )
                
                # 情報源を挿入
                for content in scraped_contents:
                    cursor.execute("""
                        INSERT INTO sources (politician_id, source_url, source_title, source_domain, scraped_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        politician_id,
                        content.get('url', ''),
                        content.get('title', ''),
                        content.get('domain', ''),
                        content.get('scraped_at', now)
                    ))
                
                conn.commit()
                logger.info(f"データベース保存完了: {search_name}")
                
        except Exception as e:
            logger.error(f"データベース保存エラー: {search_name} - {str(e)}")
            raise
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """処理統計を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 基本統計
                cursor.execute("SELECT COUNT(*) FROM politicians")
                total_politicians = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM politicians WHERE extracted_name != ''")
                successful_extractions = cursor.fetchone()[0]
                
                cursor.execute("SELECT confidence_level, COUNT(*) FROM politicians GROUP BY confidence_level")
                confidence_stats = dict(cursor.fetchall())
                
                cursor.execute("SELECT current_party, COUNT(*) FROM politicians WHERE current_party != '' GROUP BY current_party ORDER BY COUNT(*) DESC LIMIT 10")
                party_stats = dict(cursor.fetchall())
                
                return {
                    'total_politicians': total_politicians,
                    'successful_extractions': successful_extractions,
                    'success_rate': (successful_extractions / total_politicians * 100) if total_politicians > 0 else 0,
                    'confidence_stats': confidence_stats,
                    'top_parties': party_stats
                }
                
        except Exception as e:
            logger.error(f"統計取得エラー: {str(e)}")
            return {}
    
    def export_politicians_data(self, output_file: str = "politicians_export.json") -> bool:
        """政治家データをJSONエクスポート"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM politicians ORDER BY search_name
                """)
                politicians = cursor.fetchall()
                
                export_data = []
                for politician in politicians:
                    politician_dict = dict(politician)
                    politician_id = politician['id']
                    
                    # 関連データを取得
                    cursor.execute("SELECT party_name FROM party_history WHERE politician_id = ? ORDER BY order_index", (politician_id,))
                    politician_dict['party_history'] = [row[0] for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT position_name FROM positions WHERE politician_id = ? ORDER BY order_index", (politician_id,))
                    politician_dict['positions'] = [row[0] for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT school_name FROM education WHERE politician_id = ? ORDER BY order_index", (politician_id,))
                    politician_dict['education'] = [row[0] for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT career_item FROM career WHERE politician_id = ? ORDER BY order_index", (politician_id,))
                    politician_dict['career'] = [row[0] for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT source_url, source_title FROM sources WHERE politician_id = ?", (politician_id,))
                    politician_dict['sources'] = [{'url': row[0], 'title': row[1]} for row in cursor.fetchall()]
                    
                    export_data.append(politician_dict)
                
                # JSONファイルに保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"データエクスポート完了: {output_file} ({len(export_data)}件)")
                return True
                
        except Exception as e:
            logger.error(f"データエクスポートエラー: {str(e)}")
            return False