"""
M3U playlist parsing and generation utilities
"""

import re
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
import m3u8
import requests
from io import StringIO

from core.config import get_settings

logger = logging.getLogger(__name__)


class M3UParser:
    """M3U playlist parser and generator"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def parse_m3u_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse M3U content and extract channel information"""
        channels = []
        lines = content.strip().split('\n')
        
        current_info = {}
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#') and not line.startswith('#EXTINF'):
                if line.startswith('#EXTM3U'):
                    continue
                continue
            
            if line.startswith('#EXTINF'):
                # Parse EXTINF line
                current_info = self._parse_extinf_line(line)
            elif line and not line.startswith('#'):
                # This should be a URL
                if current_info:
                    current_info['stream_url'] = line
                    channels.append(current_info.copy())
                    current_info = {}
                else:
                    # URL without EXTINF, create basic entry
                    channels.append({
                        'name': self._extract_name_from_url(line),
                        'stream_url': line,
                        'group_title': 'Unknown'
                    })
        
        logger.info(f"Parsed {len(channels)} channels from M3U content")
        return channels
    
    def _parse_extinf_line(self, line: str) -> Dict[str, Any]:
        """Parse EXTINF line and extract metadata"""
        # Example: #EXTINF:-1 tvg-id="channel1" tvg-name="Channel 1" tvg-logo="logo.png" group-title="News",Channel 1 HD
        
        channel_info = {
            'name': '',
            'group_title': '',
            'logo': '',
            'tvg_id': '',
            'tvg_name': '',
            'tvg_logo': '',
            'tvg_epg': ''
        }
        
        # Extract attributes from EXTINF line
        # Pattern to match key="value" or key=value
        attr_pattern = r'(\w+(?:-\w+)*)=["\'](.*?)["\']|(\w+(?:-\w+)*)=(\S+)'
        matches = re.findall(attr_pattern, line)
        
        for match in matches:
            if match[0] and match[1]:  # key="value"
                key, value = match[0], match[1]
            elif match[2] and match[3]:  # key=value
                key, value = match[2], match[3]
            else:
                continue
            
            key = key.lower().replace('-', '_')
            if key in channel_info:
                channel_info[key] = value
        
        # Extract channel name (after the last comma)
        name_match = re.search(r',(.+)$', line)
        if name_match:
            channel_info['name'] = name_match.group(1).strip()
        
        return channel_info
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract a reasonable name from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        if path:
            # Get the last part of the path
            name = path.split('/')[-1]
            # Remove file extension
            name = name.split('.')[0]
            return name if name else "Unknown Channel"
        
        return "Unknown Channel"
    
    def parse_m3u_from_url(self, url: str) -> List[Dict[str, Any]]:
        """Download and parse M3U playlist from URL"""
        try:
            headers = {
                'User-Agent': self.settings.http_user_agent
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.settings.http_timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Handle different encodings
            content = response.text
            
            return self.parse_m3u_content(content)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching M3U from URL {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing M3U from URL {url}: {e}")
            raise
    
    def parse_m3u_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse M3U playlist from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_m3u_content(content)
            
        except UnicodeDecodeError:
            # Try with latin-1 encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return self.parse_m3u_content(content)
            except Exception as e:
                logger.error(f"Error reading M3U file {file_path}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error parsing M3U file {file_path}: {e}")
            raise
    
    def generate_m3u_content(self, channels: List[Dict[str, Any]]) -> str:
        """Generate M3U playlist content from channel list"""
        lines = ['#EXTM3U']
        
        for channel in channels:
            # Build EXTINF line
            extinf_parts = ['#EXTINF:-1']
            
            # Add attributes
            for attr in ['tvg_id', 'tvg_name', 'tvg_logo', 'tvg_epg', 'group_title']:
                value = channel.get(attr, '')
                if value:
                    attr_name = attr.replace('_', '-')
                    extinf_parts.append(f'{attr_name}="{value}"')
            
            # Add channel name
            channel_name = channel.get('name', 'Unknown')
            extinf_line = ' '.join(extinf_parts) + f',{channel_name}'
            
            lines.append(extinf_line)
            lines.append(channel.get('stream_url', ''))
        
        return '\n'.join(lines)
    
    def save_m3u_file(self, channels: List[Dict[str, Any]], file_path: str):
        """Save channels to M3U file"""
        content = self.generate_m3u_content(channels)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved {len(channels)} channels to {file_path}")
        except Exception as e:
            logger.error(f"Error saving M3U file {file_path}: {e}")
            raise
    
    def deduplicate_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate channels based on stream URL and name"""
        seen_urls = set()
        seen_names = set()
        unique_channels = []
        
        for channel in channels:
            url = channel.get('stream_url', '')
            name = channel.get('name', '')
            group = channel.get('group_title', '')
            
            # Create unique key combining name and group
            name_key = f"{name.lower()}:{group.lower()}"
            
            # Skip if we've seen this URL or name+group combination
            if url in seen_urls:
                logger.debug(f"Skipping duplicate URL: {url}")
                continue
            
            if name_key in seen_names:
                logger.debug(f"Skipping duplicate channel: {name} ({group})")
                continue
            
            seen_urls.add(url)
            seen_names.add(name_key)
            unique_channels.append(channel)
        
        removed_count = len(channels) - len(unique_channels)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate channels")
        
        return unique_channels
