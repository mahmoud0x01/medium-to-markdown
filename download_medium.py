#!/usr/bin/env python3
"""
Tool to download Medium articles as markdown with images.

Usage:
    python download_medium.py <medium_url> [output_file]
    
Example:
    python download_medium.py https://medium.com/@user/article-title output.md
"""

import re
import sys
import os
import subprocess
import requests
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import html2text
from typing import Optional, List, Tuple


class MediumDownloader:
    def __init__(self, media_dir: str = "_media"):
        """Initialize the Medium downloader.
        
        Args:
            media_dir: Directory to store downloaded images
        """
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        # More complete browser headers to bypass Medium's anti-scraping
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        })
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # Don't wrap lines
        
    def fetch_article(self, url: str) -> Tuple[str, str]:
        """Fetch the Medium article HTML.
        
        Args:
            url: Medium article URL
            
        Returns:
            Tuple of (html_content, article_title)
        """
        # Handle medium.com URLs - they might need special handling
        if 'medium.com' in url:
            # Try multiple methods to bypass Medium's restrictions
            
            # Method 1: Try direct access with improved headers
            try:
                # Update referer to medium.com for better success
                headers = self.session.headers.copy()
                headers['Referer'] = 'https://medium.com/'
                headers['Sec-Fetch-Site'] = 'same-origin'
                
                response = self.session.get(url, timeout=30, headers=headers, allow_redirects=True)
                
                # Check if we got blocked
                if response.status_code == 403:
                    print("Warning: Got 403, trying alternative method...")
                    # Method 2: Try accessing through RSS feed format
                    return self._fetch_via_rss(url)
                
                response.raise_for_status()
                
                # Check if response contains actual content or a blocking page
                if 'Access Denied' in response.text or '403' in response.text:
                    print("Warning: Access denied, trying alternative method...")
                    return self._fetch_via_rss(url)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find the article content
                # Medium uses various structures, try common ones
                article = soup.find('article')
                if not article:
                    # Try alternative structures
                    article = soup.find('div', {'role': 'article'})
                if not article:
                    # Try finding by class names common in Medium
                    article = soup.find('div', class_=re.compile(r'article|post|story'))
                if not article:
                    # Fallback to body
                    article = soup.find('body')
                
                # Extract title
                title = None
                title_tag = soup.find('h1')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                if not title:
                    meta_title = soup.find('meta', property='og:title')
                    if meta_title:
                        title = meta_title.get('content', 'Untitled')
                if not title:
                    meta_title = soup.find('meta', {'name': 'twitter:title'})
                    if meta_title:
                        title = meta_title.get('content', 'Untitled')
                if not title:
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                if not title:
                    title = "Untitled Article"
                
                return str(article) if article else response.text, title
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print("Warning: Got 403, trying alternative method...")
                    return self._fetch_via_rss(url)
                raise
        
        else:
            # Generic URL handling
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('article') or soup.find('main') or soup.find('body')
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else "Untitled Article"
            return str(article) if article else response.text, title_text
    
    def _fetch_via_rss(self, url: str) -> Tuple[str, str]:
        """Try to fetch article via Medium RSS or alternative method.
        
        Args:
            url: Medium article URL
            
        Returns:
            Tuple of (html_content, article_title)
        """
        # Try accessing via feed.medium.com or other alternative endpoints
        # Extract article ID from URL
        article_id = url.split('/')[-1] if '/' in url else url.split('-')[-1]
        
        # Try accessing with different URL format
        # Some Medium articles can be accessed via their canonical URL
        try:
            # Try with /feed/ prefix or other variations
            alt_urls = [
                url.replace('medium.com/', 'medium.com/feed/'),
                f"https://medium.com/@{url.split('@')[1].split('/')[0]}/feed" if '@' in url else None,
            ]
            
            for alt_url in alt_urls:
                if not alt_url:
                    continue
                try:
                    response = self.session.get(alt_url, timeout=30, allow_redirects=True)
                    if response.status_code == 200:
                        # Parse RSS feed
                        soup = BeautifulSoup(response.text, 'xml')
                        items = soup.find_all('item')
                        for item in items:
                            link = item.find('link')
                            if link and article_id in link.text:
                                # Found the article in RSS
                                content = item.find('content:encoded')
                                title = item.find('title')
                                if content:
                                    return content.text, title.text if title else "Untitled"
                except:
                    continue
        except:
            pass
        
        # If RSS method fails, try using a public API or service
        # As a last resort, try accessing with even more browser-like behavior
        try:
            # Simulate a browser visit by first going to medium.com
            self.session.get('https://medium.com/', timeout=10)
            import time
            time.sleep(1)  # Small delay to seem more human-like
            
            # Now try the article
            headers = self.session.headers.copy()
            headers['Referer'] = 'https://medium.com/'
            response = self.session.get(url, timeout=30, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                article = soup.find('article') or soup.find('div', {'role': 'article'}) or soup.find('body')
                title = soup.find('h1') or soup.find('title')
                title_text = title.get_text(strip=True) if title else "Untitled Article"
                return str(article) if article else response.text, title_text
        except:
            pass
        
        # Last resort: Try using curl which sometimes works better
        try:
            print("Trying curl as last resort...")
            curl_cmd = [
                'curl', '-s', '-L',
                '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                '-H', 'Referer: https://medium.com/',
                url
            ]
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout:
                soup = BeautifulSoup(result.stdout, 'html.parser')
                article = soup.find('article') or soup.find('div', {'role': 'article'}) or soup.find('body')
                title = soup.find('h1') or soup.find('title')
                title_text = title.get_text(strip=True) if title else "Untitled Article"
                return str(article) if article else result.stdout, title_text
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            pass
        
        # If all methods fail, raise an error with helpful message
        raise Exception(
            "Unable to fetch article. Medium is blocking automated access.\n\n"
            "Possible solutions:\n"
            "1. Install and use 'medium-to-markdown' npm package:\n"
            "   npm install -g medium-to-markdown\n"
            "   medium-to-markdown <url>\n\n"
            "2. Use a browser extension like 'MarkDownload' or 'SingleFile'\n\n"
            "3. Try using a VPN or different network\n\n"
            "4. Access the article in a browser first, then use browser dev tools\n\n"
            "5. If you have access, try using Medium's API or RSS feed directly"
        )
    
    def extract_images(self, html: str, base_url: str) -> List[Tuple[str, str]]:
        """Extract image URLs from HTML.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of tuples (original_url, local_filename)
        """
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        seen_urls = set()
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # Resolve relative URLs
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            # Skip data URIs and already processed images
            if src.startswith('data:') or src in seen_urls:
                continue
            
            seen_urls.add(src)
            
            # Generate local filename
            parsed = urlparse(src)
            filename = os.path.basename(parsed.path)
            if not filename or '.' not in filename:
                # Generate filename from URL hash
                filename = f"image_{hash(src) % 1000000}.jpg"
            
            # Ensure unique filename
            counter = 1
            original_filename = filename
            while (self.media_dir / filename).exists():
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1
            
            images.append((src, filename))
        
        return images
    
    def download_image(self, url: str, filename: str) -> bool:
        """Download an image from URL.
        
        Args:
            url: Image URL
            filename: Local filename to save as
            
        Returns:
            True if successful, False otherwise
        """
        # Try with requests first
        try:
            # Use image-specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://medium.com/',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            response = self.session.get(url, timeout=30, stream=True, headers=headers)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"Warning: {url} doesn't appear to be an image (content-type: {content_type})")
                return False
            
            filepath = self.media_dir / filename
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {filename}")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                # Try with curl as fallback
                try:
                    print(f"Trying curl for image: {filename}")
                    filepath = self.media_dir / filename
                    curl_cmd = [
                        'curl', '-s', '-L', '-o', str(filepath),
                        '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        '-H', 'Accept: image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                        '-H', 'Referer: https://medium.com/',
                        url
                    ]
                    result = subprocess.run(curl_cmd, timeout=30, check=True)
                    if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
                        print(f"Downloaded via curl: {filename}")
                        return True
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            print(f"Error downloading {url}: {e}")
            return False
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def convert_to_markdown(self, html: str, base_url: str) -> str:
        """Convert HTML to markdown and update image references.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Markdown content with updated image references
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract and download images
        images = self.extract_images(html, base_url)
        image_map = {}
        
        for img_url, local_filename in images:
            if self.download_image(img_url, local_filename):
                image_map[img_url] = local_filename
        
        # Update image src attributes in HTML
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # Resolve URL
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            # Update to local path if downloaded
            if src in image_map:
                img['src'] = f"{self.media_dir}/{image_map[src]}"
        
        # Convert to markdown
        markdown = self.h2t.handle(str(soup))
        
        # Post-process: update image paths in markdown
        # html2text might use different formats, so we'll update them
        for img_url, local_filename in image_map.items():
            # Update various markdown image formats
            local_path = f"{self.media_dir}/{local_filename}"
            markdown = markdown.replace(img_url, local_path)
            # Also handle if html2text uses relative paths
            markdown = re.sub(
                rf'!\[([^\]]*)\]\({re.escape(img_url)}\)',
                rf'![\1]({local_path})',
                markdown
            )
        
        return markdown
    
    def download_article(self, url: str, output_file: Optional[str] = None) -> str:
        """Download a Medium article as markdown.
        
        Args:
            url: Medium article URL
            output_file: Optional output filename (default: auto-generated)
            
        Returns:
            Path to the saved markdown file
        """
        print(f"Fetching article from: {url}")
        html, title = self.fetch_article(url)
        
        print(f"Article title: {title}")
        print("Converting to markdown and downloading images...")
        
        markdown = self.convert_to_markdown(html, url)
        
        # Generate output filename if not provided
        if not output_file:
            # Sanitize title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            output_file = f"{safe_title}.md"
        
        # Add title as header if not present
        if not markdown.strip().startswith('#'):
            markdown = f"# {title}\n\n{markdown}"
        
        # Save markdown file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"Saved markdown to: {output_path}")
        return str(output_path)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    downloader = MediumDownloader()
    try:
        downloader.download_article(url, output_file)
        print("\nDone!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

