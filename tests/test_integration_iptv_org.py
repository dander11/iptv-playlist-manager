"""
Integration test for IPTV-org playlist processing

This test downloads and processes the real IPTV-org playlist
to verify the complete functionality of the system.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.m3u_parser import M3UParser
from services.validation import ValidationService


class TestIPTVOrgIntegration:
    """Integration tests using the IPTV-org playlist"""
    
    @pytest.fixture
    def m3u_parser(self):
        return M3UParser()
    
    @pytest.fixture  
    def validation_service(self):
        return ValidationService()
    
    @pytest.mark.asyncio
    async def test_parse_iptv_org_playlist(self, m3u_parser):
        """Test parsing the actual IPTV-org playlist"""
        url = "https://iptv-org.github.io/iptv/index.m3u"
        
        try:
            channels = m3u_parser.parse_m3u_from_url(url)
            
            # Basic validation
            assert len(channels) > 0, "Should parse at least some channels"
            
            # Check structure of first channel
            first_channel = channels[0]
            required_fields = ['name', 'stream_url']
            for field in required_fields:
                assert field in first_channel, f"Channel should have {field} field"
            
            # Verify we have various groups
            groups = set(ch.get('group_title', '') for ch in channels)
            assert len(groups) > 1, "Should have multiple channel groups"
            
            print(f"✅ Successfully parsed {len(channels)} channels from IPTV-org")
            print(f"📊 Found {len(groups)} unique groups")
            
            # Show sample channels
            print("\n📺 Sample channels:")
            for i, channel in enumerate(channels[:5]):
                name = channel.get('name', 'Unknown')
                group = channel.get('group_title', 'No Group')
                url = channel.get('stream_url', '')[:50] + '...' if len(channel.get('stream_url', '')) > 50 else channel.get('stream_url', '')
                print(f"  {i+1}. {name} ({group}) - {url}")
            
        except Exception as e:
            pytest.fail(f"Failed to parse IPTV-org playlist: {e}")
    
    @pytest.mark.asyncio
    async def test_validate_sample_streams(self, validation_service):
        """Test validation of a few sample streams"""
        
        # Sample URLs to test (using common working streams)
        test_urls = [
            "https://iptv-org.github.io/iptv/index.m3u",  # The playlist itself
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # YouTube (should fail gracefully)
            "https://httpbin.org/status/200",  # Should return 200
            "https://httpbin.org/status/404",  # Should return 404
        ]
        
        results = []
        
        for url in test_urls:
            try:
                is_working, response_time, error_msg, status_code = await validation_service.validate_stream_url(url)
                results.append({
                    'url': url,
                    'working': is_working,
                    'response_time': response_time,
                    'error': error_msg,
                    'status': status_code
                })
                
                print(f"🔍 {url[:50]}... -> {'✅' if is_working else '❌'} ({response_time:.2f}s)")
                
            except Exception as e:
                print(f"❌ Error validating {url}: {e}")
        
        # At least one URL should work (the playlist itself or httpbin/200)
        working_count = sum(1 for r in results if r['working'])
        assert working_count > 0, "At least one test URL should be working"
        
        print(f"\n✅ Validation test completed: {working_count}/{len(test_urls)} URLs working")
    
    def test_deduplication(self, m3u_parser):
        """Test channel deduplication logic"""
        
        # Create test channels with duplicates
        test_channels = [
            {
                'name': 'BBC One',
                'group_title': 'UK',
                'stream_url': 'http://example.com/bbc1'
            },
            {
                'name': 'BBC One',  # Duplicate name+group
                'group_title': 'UK',
                'stream_url': 'http://another.com/bbc1'
            },
            {
                'name': 'CNN',
                'group_title': 'News',
                'stream_url': 'http://example.com/cnn'
            },
            {
                'name': 'CNN International',
                'group_title': 'News', 
                'stream_url': 'http://example.com/cnn'  # Duplicate URL
            },
            {
                'name': 'Sky News',
                'group_title': 'News',
                'stream_url': 'http://example.com/sky'
            }
        ]
        
        # Test deduplication
        unique_channels = m3u_parser.deduplicate_channels(test_channels)
        
        # Should remove duplicates
        assert len(unique_channels) < len(test_channels), "Should remove some duplicates"
        assert len(unique_channels) >= 3, "Should keep at least 3 unique channels"
        
        # Check URLs are unique
        urls = [ch['stream_url'] for ch in unique_channels]
        assert len(urls) == len(set(urls)), "All URLs should be unique"
        
        print(f"✅ Deduplication test passed: {len(test_channels)} -> {len(unique_channels)} channels")
    
    def test_m3u_generation(self, m3u_parser):
        """Test M3U playlist generation"""
        
        test_channels = [
            {
                'name': 'BBC One HD',
                'group_title': 'UK',
                'tvg_id': 'bbc1.uk',
                'tvg_logo': 'https://example.com/bbc1.png',
                'stream_url': 'http://example.com/bbc1'
            },
            {
                'name': 'CNN',
                'group_title': 'News',
                'stream_url': 'http://example.com/cnn'
            }
        ]
        
        # Generate M3U content
        m3u_content = m3u_parser.generate_m3u_content(test_channels)
        
        # Basic validation
        assert m3u_content.startswith('#EXTM3U'), "Should start with #EXTM3U"
        assert 'BBC One HD' in m3u_content, "Should contain channel names"
        assert 'http://example.com/bbc1' in m3u_content, "Should contain stream URLs"
        assert 'group-title="UK"' in m3u_content, "Should contain group information"
        
        # Count lines
        lines = m3u_content.split('\n')
        extinf_lines = [line for line in lines if line.startswith('#EXTINF')]
        assert len(extinf_lines) == len(test_channels), "Should have EXTINF line for each channel"
        
        print("✅ M3U generation test passed")
        print(f"📄 Generated {len(lines)} lines for {len(test_channels)} channels")


if __name__ == "__main__":
    # Run the tests directly
    pytest.main([__file__, "-v"])
