"""
Whitepaper and Documentation Analyzer
Analyzes project documentation to extract contract addresses and project intelligence
"""

import re
import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import json
from utils.llm import analyze_text

class WhitepaperAnalyzer:
    """Analyzes whitepapers and project docs for contract addresses and project intelligence"""

    def __init__(self):
        self.contract_address_patterns = [
            r'0x[a-fA-F0-9]{40}',  # Standard Ethereum address
            r'Contract[:\s]*0x[a-fA-F0-9]{40}',  # "Contract: 0x..."
            r'Token[:\s]*0x[a-fA-F0-9]{40}',     # "Token: 0x..."
            r'Address[:\s]*0x[a-fA-F0-9]{40}',   # "Address: 0x..."
        ]

    def research_token_project(self, token_symbol: str) -> Dict:
        """
        Comprehensive token research including whitepaper analysis
        Returns contract addresses, project info, and legitimacy assessment
        """
        print(f"📄 Starting comprehensive research for {token_symbol}...")

        research_results = {
            'token_symbol': token_symbol,
            'contract_addresses': {},
            'project_info': {},
            'documentation_sources': [],
            'legitimacy_score': 0.0,
            'research_confidence': 0.0,
            'red_flags': [],
            'green_flags': []
        }

        # Step 1: Find official project sources
        official_sources = self._find_official_sources(token_symbol)
        research_results['documentation_sources'] = official_sources

        # Step 2: Analyze each source for contract addresses
        for source in official_sources:
            try:
                addresses = self._extract_addresses_from_source(source)
                if addresses:
                    print(f"✅ Found addresses in {source['type']}: {addresses}")
                    research_results['contract_addresses'].update(addresses)
            except Exception as e:
                print(f"⚠️ Error analyzing {source['type']}: {e}")

        # Step 3: Analyze project legitimacy
        legitimacy_analysis = self._analyze_project_legitimacy(official_sources, research_results)
        research_results.update(legitimacy_analysis)

        # Step 4: Validate discovered addresses
        validated_addresses = self._validate_contract_addresses(research_results['contract_addresses'])
        research_results['contract_addresses'] = validated_addresses

        print(f"📊 Research complete for {token_symbol}:")
        print(f"   • Addresses found: {len(validated_addresses)}")
        print(f"   • Legitimacy score: {research_results['legitimacy_score']:.1f}/10")
        print(f"   • Research confidence: {research_results['research_confidence']:.1%}")

        return research_results

    def _find_official_sources(self, token_symbol: str) -> List[Dict]:
        """Find official project sources (website, whitepaper, GitHub, etc.)"""
        sources = []

        # Strategy 1: Search for official website via multiple channels
        website_searches = [
            f"{token_symbol} token official website",
            f"{token_symbol} cryptocurrency project",
            f"{token_symbol} whitepaper",
            f"{token_symbol} token contract address",
        ]

        for search_query in website_searches:
            try:
                # Use DuckDuckGo to find official sources
                results = self._search_web(search_query)
                for result in results[:3]:  # Top 3 results per query
                    if self._looks_like_official_source(result, token_symbol):
                        source_info = {
                            'url': result['url'],
                            'title': result.get('title', ''),
                            'type': 'official_website',
                            'confidence': self._calculate_source_confidence(result, token_symbol)
                        }
                        sources.append(source_info)
            except Exception as e:
                print(f"⚠️ Web search error for {search_query}: {e}")

        # Strategy 2: Look for documentation on common platforms
        doc_platforms = [
            f"https://docs.{token_symbol.lower()}.com",
            f"https://github.com/{token_symbol.lower()}",
            f"https://whitepaper.{token_symbol.lower()}.com",
            f"https://{token_symbol.lower()}.gitbook.io",
        ]

        for url in doc_platforms:
            try:
                if self._url_exists(url):
                    sources.append({
                        'url': url,
                        'title': f"{token_symbol} Documentation",
                        'type': 'documentation',
                        'confidence': 0.7
                    })
            except Exception:
                continue

        # Remove duplicates and sort by confidence
        unique_sources = []
        seen_urls = set()
        for source in sources:
            if source['url'] not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(source['url'])

        return sorted(unique_sources, key=lambda x: x['confidence'], reverse=True)[:5]

    def _search_web(self, query: str) -> List[Dict]:
        """Search web for project information"""
        try:
            # Use DuckDuckGo instant answers API (no key required)
            response = requests.get(
                'https://api.duckduckgo.com/',
                params={
                    'q': query,
                    'format': 'json',
                    'no_html': '1',
                    'skip_disambig': '1'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                # Extract results from various DuckDuckGo response formats
                if 'Results' in data:
                    for result in data['Results'][:3]:
                        results.append({
                            'url': result.get('FirstURL', ''),
                            'title': result.get('Text', ''),
                            'snippet': result.get('Result', '')
                        })

                if 'RelatedTopics' in data:
                    for topic in data['RelatedTopics'][:2]:
                        if isinstance(topic, dict) and 'FirstURL' in topic:
                            results.append({
                                'url': topic.get('FirstURL', ''),
                                'title': topic.get('Text', ''),
                                'snippet': topic.get('Result', '')
                            })

                return results

        except Exception as e:
            print(f"⚠️ Web search failed: {e}")

        return []

    def _looks_like_official_source(self, result: Dict, token_symbol: str) -> bool:
        """Determine if a search result looks like an official source"""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()

        # Positive indicators
        official_indicators = [
            token_symbol.lower() in url,
            'official' in title,
            'whitepaper' in title,
            'docs' in url,
            'github.com' in url,
            'gitbook.io' in url
        ]

        # Negative indicators
        spam_indicators = [
            'coinmarketcap.com' in url,
            'coingecko.com' in url,
            'reddit.com' in url,
            'twitter.com' in url,
            'telegram' in url,
            'scam' in title,
            'fake' in title
        ]

        positive_score = sum(official_indicators)
        negative_score = sum(spam_indicators)

        return positive_score > negative_score and positive_score > 0

    def _calculate_source_confidence(self, result: Dict, token_symbol: str) -> float:
        """Calculate confidence score for a source"""
        confidence = 0.5  # Base confidence

        url = result.get('url', '').lower()
        title = result.get('title', '').lower()

        # Boost confidence for official indicators
        if token_symbol.lower() in url:
            confidence += 0.3
        if 'official' in title or 'whitepaper' in title:
            confidence += 0.2
        if any(domain in url for domain in ['github.com', 'gitbook.io', 'docs.']):
            confidence += 0.15

        # Reduce confidence for questionable sources
        if any(domain in url for domain in ['reddit.com', 'twitter.com', 'telegram']):
            confidence -= 0.2

        return min(confidence, 0.95)

    def _url_exists(self, url: str) -> bool:
        """Check if URL exists and is accessible"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code < 400
        except:
            return False

    def _extract_addresses_from_source(self, source: Dict) -> Dict[str, str]:
        """Extract contract addresses from a documentation source"""
        addresses = {}

        try:
            print(f"🔍 Analyzing {source['type']}: {source['url']}")

            # Fetch the content
            try:
                content_analysis = self._fetch_and_analyze_webpage(source['url'])

                if content_analysis:
                    # Use regex to find addresses in the analysis
                    for pattern in self.contract_address_patterns:
                        matches = re.findall(pattern, content_analysis, re.IGNORECASE)
                        for match in matches:
                            if match.startswith('0x') and len(match) == 42:
                                # Try to determine which chain this address belongs to
                                chain = self._guess_chain_from_context(content_analysis, match)
                                addresses[chain] = match
                                print(f"✅ Found {chain} address: {match}")

                    # Also use LLM to analyze for addresses
                    llm_analysis = self._llm_extract_addresses(content_analysis)
                    addresses.update(llm_analysis)

            except Exception as e:
                print(f"⚠️ Web fetch failed for {source['url']}: {e}")

        except Exception as e:
            print(f"❌ Error extracting addresses from {source['url']}: {e}")

        return addresses

    def _fetch_and_analyze_webpage(self, url: str) -> Optional[str]:
        """Fetch and analyze webpage content for contract addresses"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Parse HTML content
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract text content
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text()

                # Clean up text
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = ' '.join(chunk for chunk in chunks if chunk)

                # Limit content length for LLM analysis
                if len(text_content) > 3000:
                    text_content = text_content[:3000] + "..."

                return text_content
            else:
                print(f"⚠️ HTTP {response.status_code} for {url}")
                return None

        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")
            return None

    def _guess_chain_from_context(self, content: str, address: str) -> str:
        """Guess blockchain from context around the address"""
        content_lower = content.lower()

        # Look for chain indicators around the address
        if any(keyword in content_lower for keyword in ['bsc', 'binance', 'pancake']):
            return 'bsc'
        elif any(keyword in content_lower for keyword in ['polygon', 'matic', 'quickswap']):
            return 'polygon'
        elif any(keyword in content_lower for keyword in ['ethereum', 'eth', 'uniswap']):
            return 'ethereum'
        else:
            return 'unknown'

    def _llm_extract_addresses(self, content: str) -> Dict[str, str]:
        """Use LLM to intelligently extract contract addresses"""
        try:
            analysis_prompt = f"""
            Analyze this content and extract all cryptocurrency contract addresses.
            For each address found, identify which blockchain it belongs to.
            Return in JSON format: {{"blockchain_name": "0xaddress"}}

            Content: {content[:2000]}...
            """

            llm_result = analyze_text(analysis_prompt)

            if llm_result and isinstance(llm_result, str):
                # Try to parse JSON response
                try:
                    addresses = json.loads(llm_result)
                    if isinstance(addresses, dict):
                        print(f"🤖 LLM extracted addresses: {addresses}")
                        return addresses
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"⚠️ LLM address extraction failed: {e}")

        return {}

    def _analyze_project_legitimacy(self, sources: List[Dict], research_data: Dict) -> Dict:
        """Analyze project legitimacy based on documentation quality"""
        legitimacy_score = 5.0  # Start with neutral score
        red_flags = []
        green_flags = []

        # Analyze source quality
        if len(sources) >= 3:
            green_flags.append("Multiple official sources found")
            legitimacy_score += 1.5
        elif len(sources) == 0:
            red_flags.append("No official documentation found")
            legitimacy_score -= 3.0

        # Check for GitHub presence
        has_github = any('github.com' in s['url'] for s in sources)
        if has_github:
            green_flags.append("Active GitHub repository")
            legitimacy_score += 1.0
        else:
            red_flags.append("No GitHub repository found")
            legitimacy_score -= 0.5

        # Check for whitepaper
        has_whitepaper = any('whitepaper' in s['title'].lower() for s in sources)
        if has_whitepaper:
            green_flags.append("Whitepaper available")
            legitimacy_score += 1.0

        # Check for documentation
        has_docs = any(s['type'] == 'documentation' for s in sources)
        if has_docs:
            green_flags.append("Technical documentation available")
            legitimacy_score += 0.5

        # Calculate research confidence
        research_confidence = min(0.95, len(sources) * 0.15 + len(research_data['contract_addresses']) * 0.2)

        return {
            'legitimacy_score': max(0, min(10, legitimacy_score)),
            'research_confidence': research_confidence,
            'red_flags': red_flags,
            'green_flags': green_flags
        }

    def _validate_contract_addresses(self, addresses: Dict[str, str]) -> Dict[str, str]:
        """Validate that discovered addresses are actual contracts"""
        validated = {}

        for chain, address in addresses.items():
            if self._is_valid_contract_address(address):
                validated[chain] = address
                print(f"✅ Validated {chain} contract: {address}")
            else:
                print(f"❌ Invalid contract address for {chain}: {address}")

        return validated

    def _is_valid_contract_address(self, address: str) -> bool:
        """Basic validation of contract address format"""
        if not address or not isinstance(address, str):
            return False

        # Check format
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return False

        # Check it's not a common null address
        null_addresses = [
            '0x0000000000000000000000000000000000000000',
            '0x000000000000000000000000000000000000dead',
        ]

        return address.lower() not in [addr.lower() for addr in null_addresses]

# Global whitepaper analyzer
whitepaper_analyzer = WhitepaperAnalyzer()

def research_token_comprehensively(token_symbol: str) -> Dict:
    """Research token comprehensively including whitepaper analysis"""
    return whitepaper_analyzer.research_token_project(token_symbol)

def find_contract_via_research(token_symbol: str) -> Optional[str]:
    """Find contract address via comprehensive research"""
    research = research_token_comprehensively(token_symbol)

    # Return the most likely contract address
    if research['contract_addresses']:
        # Prefer BSC for Asian tokens, then Ethereum, then others
        chain_priority = ['bsc', 'ethereum', 'polygon', 'unknown']

        for chain in chain_priority:
            if chain in research['contract_addresses']:
                return research['contract_addresses'][chain]

        # Return any address if no priority match
        return next(iter(research['contract_addresses'].values()))

    return None

def get_project_legitimacy(token_symbol: str) -> Dict:
    """Get project legitimacy assessment"""
    research = research_token_comprehensively(token_symbol)

    return {
        'legitimacy_score': research['legitimacy_score'],
        'research_confidence': research['research_confidence'],
        'red_flags': research['red_flags'],
        'green_flags': research['green_flags'],
        'has_documentation': len(research['documentation_sources']) > 0,
        'contract_addresses_found': len(research['contract_addresses'])
    }