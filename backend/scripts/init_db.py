"""
Database initialization script
Creates default admin user and sample data
"""

import asyncio
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import init_db, get_db, User
from core.auth import get_password_hash
from core.config import get_settings


async def create_default_admin():
    """Create default admin user"""
    
    # Initialize database
    await init_db()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("Default admin user already exists")
            return
        
        # Create default admin user
        admin_user = User(
            username="admin",
            email="admin@localhost",
            hashed_password=get_password_hash("admin"),
            is_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("Default admin user created successfully")
        print("Username: admin")
        print("Password: admin")
        print("Please change the password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


async def setup_sample_playlist():
    """Setup sample playlist from IPTV-org"""
    
    db = next(get_db())
    
    try:
        from core.database import Playlist, Channel
        from services.m3u_parser import M3UParser
        
        # Check if sample playlist already exists
        existing_playlist = db.query(Playlist).filter(Playlist.name == "IPTV-org Sample").first()
        
        if existing_playlist:
            print("Sample playlist already exists")
            return
        
        # Create sample playlist
        sample_playlist = Playlist(
            name="IPTV-org Sample",
            description="Sample playlist from IPTV-org for testing",
            source_url="https://iptv-org.github.io/iptv/index.m3u"
        )
        
        db.add(sample_playlist)
        db.commit()
        db.refresh(sample_playlist)
        
        print("Sample playlist created successfully")
        print("You can now test the validation with the IPTV-org sample data")
        
        # Try to fetch and parse the sample playlist
        try:
            parser = M3UParser()
            channels_data = parser.parse_m3u_from_url(sample_playlist.source_url)
            
            # Add first 10 channels as examples
            for i, channel_data in enumerate(channels_data[:10]):
                channel = Channel(
                    playlist_id=sample_playlist.id,
                    name=channel_data.get('name', f'Channel {i+1}'),
                    group_title=channel_data.get('group_title', 'Sample'),
                    logo=channel_data.get('logo', ''),
                    tvg_id=channel_data.get('tvg_id', ''),
                    tvg_name=channel_data.get('tvg_name', ''),
                    tvg_logo=channel_data.get('tvg_logo', ''),
                    tvg_epg=channel_data.get('tvg_epg', ''),
                    stream_url=channel_data.get('stream_url', '')
                )
                db.add(channel)
            
            db.commit()
            print(f"Added {min(10, len(channels_data))} sample channels")
            
        except Exception as e:
            print(f"Warning: Could not fetch sample channels: {e}")
        
    except Exception as e:
        print(f"Error creating sample playlist: {e}")
        db.rollback()
    finally:
        db.close()


async def main():
    """Main initialization function"""
    print("Initializing IPTV Playlist Manager...")
    
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    
    # Create default admin user
    await create_default_admin()
    
    # Setup sample playlist
    await setup_sample_playlist()
    
    print("Initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())
