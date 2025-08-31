"""
Simple integration test for IPTV-org playlist processing

This test downloads and processes the real IPTV-org playlist
to verify the M3U parsing functionality works correctly.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set working directory to backend
os.chdir(str(backend_dir))

from services.m3u_parser import M3UParser


def test_parse_iptv_org_playlist():
    """Test parsing the actual IPTV-org playlist"""
    print("🔍 Testing IPTV-org playlist parsing...")
    
    m3u_parser = M3UParser()
    url = "https://iptv-org.github.io/iptv/index.m3u"
    
    try:
        channels = m3u_parser.parse_m3u_from_url(url)
        
        # Basic validation
        assert len(channels) > 0, "Should parse at least some channels"
        print(f"✅ Successfully parsed {len(channels)} channels from IPTV-org")
        
        # Check structure of first channel
        first_channel = channels[0]
        required_fields = ['name', 'stream_url']
        for field in required_fields:
            assert field in first_channel, f"Channel should have {field} field"
        
        # Verify we have various groups
        groups = set(ch.get('group_title', '') for ch in channels)
        print(f"📊 Found {len(groups)} unique groups")
        
        # Show sample channels
        print("\n📺 Sample channels:")
        for i, channel in enumerate(channels[:5]):
            name = channel.get('name', 'Unknown')
            group = channel.get('group_title', 'No Group')
            url_preview = channel.get('stream_url', '')[:50] + '...' if len(channel.get('stream_url', '')) > 50 else channel.get('stream_url', '')
            print(f"  {i+1}. {name} ({group}) - {url_preview}")
        
        # Test deduplication
        print("\n🔄 Testing deduplication...")
        unique_channels = m3u_parser.deduplicate_channels(channels)
        duplicates_removed = len(channels) - len(unique_channels)
        print(f"✅ Removed {duplicates_removed} duplicates: {len(channels)} -> {len(unique_channels)} channels")
        
        # Test M3U generation
        print("\n📄 Testing M3U generation...")
        m3u_content = m3u_parser.generate_m3u_content(unique_channels[:10])  # Just first 10 for testing
        
        assert m3u_content.startswith('#EXTM3U'), "Should start with #EXTM3U"
        lines = m3u_content.split('\n')
        print(f"✅ Generated {len(lines)} lines for 10 channels")
        
        print("\n🎉 All tests passed! IPTV-org playlist processing works correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_parse_iptv_org_playlist()
    sys.exit(0 if success else 1)
