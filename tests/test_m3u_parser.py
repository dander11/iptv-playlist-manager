"""
Test M3U parsing functionality
"""

import pytest
from services.m3u_parser import M3UParser


class TestM3UParser:
    """Test M3U parsing and generation"""

    def setup_method(self):
        """Setup test instance"""
        self.parser = M3UParser()

    def test_parse_simple_m3u(self):
        """Test parsing simple M3U content"""
        content = """#EXTM3U
#EXTINF:-1 tvg-id="channel1" tvg-name="Test Channel" group-title="Test Group",Test Channel
http://example.com/stream1.m3u8
#EXTINF:-1 tvg-id="channel2" group-title="News",News Channel
http://example.com/stream2.m3u8"""
        
        channels = self.parser.parse_m3u_content(content)
        
        assert len(channels) == 2
        assert channels[0]['name'] == 'Test Channel'
        assert channels[0]['tvg_id'] == 'channel1'
        assert channels[0]['group_title'] == 'Test Group'
        assert channels[0]['stream_url'] == 'http://example.com/stream1.m3u8'
        
        assert channels[1]['name'] == 'News Channel'
        assert channels[1]['group_title'] == 'News'

    def test_parse_extinf_line(self):
        """Test parsing EXTINF line"""
        line = '#EXTINF:-1 tvg-id="test123" tvg-name="Test Channel" tvg-logo="logo.png" group-title="Entertainment",Test Channel HD'
        
        result = self.parser._parse_extinf_line(line)
        
        assert result['name'] == 'Test Channel HD'
        assert result['tvg_id'] == 'test123'
        assert result['tvg_name'] == 'Test Channel'
        assert result['tvg_logo'] == 'logo.png'
        assert result['group_title'] == 'Entertainment'

    def test_generate_m3u_content(self):
        """Test generating M3U content"""
        channels = [
            {
                'name': 'Test Channel',
                'stream_url': 'http://example.com/stream.m3u8',
                'tvg_id': 'test1',
                'group_title': 'Test'
            },
            {
                'name': 'Another Channel',
                'stream_url': 'http://example.com/stream2.m3u8',
                'group_title': 'News'
            }
        ]
        
        content = self.parser.generate_m3u_content(channels)
        
        assert content.startswith('#EXTM3U')
        assert 'Test Channel' in content
        assert 'http://example.com/stream.m3u8' in content
        assert 'tvg-id="test1"' in content
        assert 'group-title="Test"' in content

    def test_deduplicate_channels(self):
        """Test channel deduplication"""
        channels = [
            {
                'name': 'Channel 1',
                'stream_url': 'http://example.com/stream1.m3u8',
                'group_title': 'Test'
            },
            {
                'name': 'Channel 1',  # Duplicate name
                'stream_url': 'http://example.com/stream1.m3u8',  # Duplicate URL
                'group_title': 'Test'
            },
            {
                'name': 'Channel 2',
                'stream_url': 'http://example.com/stream2.m3u8',
                'group_title': 'Test'
            }
        ]
        
        unique_channels = self.parser.deduplicate_channels(channels)
        
        assert len(unique_channels) == 2
        assert unique_channels[0]['name'] == 'Channel 1'
        assert unique_channels[1]['name'] == 'Channel 2'

    def test_extract_name_from_url(self):
        """Test extracting name from URL"""
        url = "http://example.com/live/channel_name.m3u8"
        name = self.parser._extract_name_from_url(url)
        assert name == "channel_name"
        
        url2 = "http://example.com/"
        name2 = self.parser._extract_name_from_url(url2)
        assert name2 == "Unknown Channel"

    def test_parse_empty_content(self):
        """Test parsing empty content"""
        content = ""
        channels = self.parser.parse_m3u_content(content)
        assert len(channels) == 0

    def test_parse_malformed_content(self):
        """Test parsing malformed content"""
        content = """#EXTM3U
#EXTINF:-1,Channel without URL
#EXTINF:-1,Another Channel
http://example.com/stream.m3u8"""
        
        channels = self.parser.parse_m3u_content(content)
        assert len(channels) == 1
        assert channels[0]['name'] == 'Another Channel'
        assert channels[0]['stream_url'] == 'http://example.com/stream.m3u8'
