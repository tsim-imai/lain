#!/usr/bin/env python3
"""
検索エンジンのスクレイピングテストスクリプト
Brave, DuckDuckGo, Bingの各検索エンジンで簡単なテストを実行
"""

import requests
from bs4 import BeautifulSoup
import time
import sys
from urllib.parse import urlencode


def test_brave_search(query: str):
    """Brave検索のテスト"""
    print(f"\n=== Brave検索テスト: '{query}' ===")
    
    try:
        # Brave検索URL
        url = f"https://search.brave.com/search?q={query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} 文字")
        
        if response.status_code != 200:
            print(f"❌ HTTPエラー: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 複数のセレクターを試す
        selectors = [
            '.snippet',
            '[data-type="web"]',
            '.result',
            '.web-result',
            'article',
            '.fdb'
        ]
        
        results = []
        for selector in selectors:
            elements = soup.select(selector)
            print(f"セレクター '{selector}': {len(elements)}件")
            
            if elements:
                for i, elem in enumerate(elements[:3]):
                    title_elem = elem.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
                    url = title_elem.get('href', '') if title_elem else ""
                    
                    if title and len(title) > 10:
                        results.append({
                            'title': title,
                            'url': url,
                            'selector': selector
                        })
                        print(f"  {i+1}. {title[:50]}...")
                        if url:
                            print(f"      URL: {url}")
                
                if results:
                    break
        
        if not results:
            print("❌ 検索結果が見つかりませんでした")
            # デバッグ用にページタイトルを表示
            title = soup.title.string if soup.title else "タイトルなし"
            print(f"ページタイトル: {title}")
        else:
            print(f"✅ {len(results)}件の結果を取得")
        
        return results
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return []


def test_duckduckgo_search(query: str):
    """DuckDuckGo検索のテスト"""
    print(f"\n=== DuckDuckGo検索テスト: '{query}' ===")
    
    try:
        # DuckDuckGo検索URL
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} 文字")
        
        if response.status_code != 200:
            print(f"❌ HTTPエラー: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # DuckDuckGo特有のセレクターを試す
        selectors = [
            '.result',
            '.web-result',
            '.links_main',
            '.result__body',
            '.result__snippet',
            'h2.result__title',
            '.results .result'
        ]
        
        results = []
        for selector in selectors:
            elements = soup.select(selector)
            print(f"セレクター '{selector}': {len(elements)}件")
            
            if elements:
                for i, elem in enumerate(elements[:3]):
                    # タイトルを探す
                    title_elem = elem.find('a', class_='result__a') or elem.find('h2') or elem.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
                    url = title_elem.get('href', '') if title_elem else ""
                    
                    # スニペットを探す
                    snippet_elem = elem.find(class_='result__snippet') or elem.find('p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if title and len(title) > 10:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'selector': selector
                        })
                        print(f"  {i+1}. {title[:50]}...")
                        if snippet:
                            print(f"      {snippet[:60]}...")
                        if url:
                            print(f"      URL: {url}")
                
                if results:
                    break
        
        if not results:
            print("❌ 検索結果が見つかりませんでした")
            # デバッグ用にページタイトルを表示
            title = soup.title.string if soup.title else "タイトルなし"
            print(f"ページタイトル: {title}")
        else:
            print(f"✅ {len(results)}件の結果を取得")
        
        return results
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return []


def test_bing_search(query: str):
    """Bing検索のテスト（改良版）"""
    print(f"\n=== Bing検索テスト: '{query}' ===")
    
    try:
        # Bing検索URL
        params = {
            'q': query,
            'count': '10',
            'mkt': 'ja-JP',
            'setlang': 'ja'
        }
        url = f"https://www.bing.com/search?{urlencode(params)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} 文字")
        
        if response.status_code != 200:
            print(f"❌ HTTPエラー: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Bing用のセレクターを試す
        selectors = [
            '.b_algo',
            'li.b_algo',
            '.b_searchResult',
            '.b_title',
            'h2 a',
            'a[href^="http"]:not([href*="bing.com"])',
            '[data-priority]'
        ]
        
        results = []
        for selector in selectors:
            elements = soup.select(selector)
            print(f"セレクター '{selector}': {len(elements)}件")
            
            if elements and selector in ['.b_algo', 'li.b_algo', '.b_searchResult']:
                # 構造化された検索結果
                for i, elem in enumerate(elements[:3]):
                    title_elem = elem.select_one('h2 a') or elem.select_one('a')
                    title = title_elem.get_text(strip=True) if title_elem else "タイトルなし"
                    url = title_elem.get('href', '') if title_elem else ""
                    
                    snippet_elem = elem.select_one('.b_caption p') or elem.select_one('p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if title and len(title) > 10:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'selector': selector
                        })
                        print(f"  {i+1}. {title[:50]}...")
                        if snippet:
                            print(f"      {snippet[:60]}...")
                        if url:
                            print(f"      URL: {url}")
                
                if results:
                    break
            
            elif selector == 'a[href^="http"]:not([href*="bing.com"])' and not results:
                # フォールバック: 外部リンクを直接探す
                seen_urls = set()
                for i, elem in enumerate(elements[:5]):
                    href = elem.get('href', '')
                    title = elem.get_text(strip=True)
                    
                    if href and href not in seen_urls and title and len(title) > 10:
                        seen_urls.add(href)
                        results.append({
                            'title': title,
                            'url': href,
                            'snippet': "外部リンクから取得",
                            'selector': selector
                        })
                        print(f"  {i+1}. {title[:50]}...")
                        print(f"      URL: {href}")
                        
                        if len(results) >= 3:
                            break
        
        if not results:
            print("❌ 検索結果が見つかりませんでした")
            # デバッグ用にページタイトルを表示
            title = soup.title.string if soup.title else "タイトルなし"
            print(f"ページタイトル: {title}")
            
            # 利用可能な要素をいくつか表示
            all_links = soup.find_all('a', href=True)
            external_links = [a for a in all_links if a.get('href', '').startswith('http') and 'bing.com' not in a.get('href', '')]
            print(f"外部リンク総数: {len(external_links)}")
        else:
            print(f"✅ {len(results)}件の結果を取得")
        
        return results
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return []


def main():
    """メイン実行関数"""
    print("検索エンジンスクレイピングテスト開始")
    print("=" * 50)
    
    # テストクエリ
    test_queries = [
        "岸田文雄 誕生日",
        "Python プログラミング",
        "天気 東京"
    ]
    
    for query in test_queries:
        print(f"\n🔍 テストクエリ: '{query}'")
        print("=" * 50)
        
        # 各検索エンジンをテスト
        brave_results = test_brave_search(query)
        time.sleep(2)  # レート制限対策
        
        duckduckgo_results = test_duckduckgo_search(query)
        time.sleep(2)  # レート制限対策
        
        bing_results = test_bing_search(query)
        time.sleep(2)  # レート制限対策
        
        # 結果まとめ
        print(f"\n📊 '{query}' の結果まとめ:")
        print(f"  Brave: {len(brave_results)}件")
        print(f"  DuckDuckGo: {len(duckduckgo_results)}件")
        print(f"  Bing: {len(bing_results)}件")
        
        # どの検索エンジンが最も良い結果を返したか
        best_engine = "なし"
        max_results = 0
        
        for engine, results in [("Brave", brave_results), ("DuckDuckGo", duckduckgo_results), ("Bing", bing_results)]:
            if len(results) > max_results:
                max_results = len(results)
                best_engine = engine
        
        if max_results > 0:
            print(f"  最良: {best_engine} ({max_results}件)")
        else:
            print("  ⚠️ すべての検索エンジンで結果なし")
        
        print("-" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nエラーが発生しました: {e}")
        sys.exit(1)