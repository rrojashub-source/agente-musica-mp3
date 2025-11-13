#!/usr/bin/env python3
"""
Test API connections for Phase 4
Run: python scripts/test_apis.py
"""
import json
from pathlib import Path
import sys

print("🧪 Testing API Connections for Phase 4...\n")

# Load credentials
secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"

if not secrets_path.exists():
    print(f"❌ ERROR: Secrets file not found at {secrets_path}")
    print("   Please run API setup first (see docs/guides/api_setup.md)")
    sys.exit(1)

try:
    with open(secrets_path) as f:
        secrets = json.load(f)
except Exception as e:
    print(f"❌ ERROR: Could not load secrets: {e}")
    sys.exit(1)

# Test 1: YouTube API
print("1️⃣ Testing YouTube Data API v3...")
try:
    youtube_key = secrets['apis']['youtube']['api_key']
    print(f"   API Key found: ...{youtube_key[-4:]}")

    # Test connection
    import requests
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={'part': 'snippet', 'q': 'test', 'key': youtube_key, 'maxResults': 1},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            print("   ✅ YouTube API: Connected and working")
            print(f"   Test search returned {len(data['items'])} result(s)")
        else:
            print("   ⚠️  YouTube API: Connected but no results")
    elif response.status_code == 403:
        print("   ❌ YouTube API: Authentication failed")
        print("      Check if API is enabled in Google Cloud Console")
    else:
        print(f"   ❌ YouTube API: Failed (HTTP {response.status_code})")
        print(f"      Response: {response.text[:200]}")

except KeyError:
    print("   ❌ YouTube API key not found in secrets")
    print("      Run: bash ~/.claude/secrets/set-secret.sh apis youtube api_key 'YOUR_KEY'")
except ImportError:
    print("   ❌ 'requests' library not installed")
    print("      Run: pip install requests")
except Exception as e:
    print(f"   ❌ YouTube API test failed: {e}")

# Test 2: Spotify API
print("\n2️⃣ Testing Spotify Web API...")
try:
    client_id = secrets['apis']['spotify']['client_id']
    client_secret = secrets['apis']['spotify']['client_secret']
    print(f"   Client ID found: ...{client_id[-4:]}")
    print(f"   Client Secret found: ...{client_secret[-4:]}")

    # Test connection
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    ))

    results = sp.search(q='test', limit=1, type='track')

    if results and 'tracks' in results and results['tracks']['items']:
        print("   ✅ Spotify API: Connected and working")
        print(f"   Test search returned {len(results['tracks']['items'])} result(s)")
    else:
        print("   ⚠️  Spotify API: Connected but no results")

except KeyError:
    print("   ❌ Spotify credentials not found in secrets")
    print("      Run:")
    print("      bash ~/.claude/secrets/set-secret.sh apis spotify client_id 'YOUR_ID'")
    print("      bash ~/.claude/secrets/set-secret.sh apis spotify client_secret 'YOUR_SECRET'")
except ImportError:
    print("   ❌ 'spotipy' library not installed")
    print("      Run: pip install spotipy")
except Exception as e:
    print(f"   ❌ Spotify API test failed: {e}")

# Test 3: MusicBrainz API
print("\n3️⃣ Testing MusicBrainz API...")
try:
    import musicbrainzngs as mb
    mb.set_useragent("NexusMusicManager", "1.0", "https://github.com/nexus/music")

    result = mb.search_recordings(query="Bohemian Rhapsody", artist="Queen", limit=1)

    if result and 'recording-list' in result and len(result['recording-list']) > 0:
        print("   ✅ MusicBrainz API: Connected and working")
        print(f"   Test search returned {len(result['recording-list'])} result(s)")
    else:
        print("   ⚠️  MusicBrainz API: Connected but no results")

except ImportError:
    print("   ❌ 'musicbrainzngs' library not installed")
    print("      Run: pip install musicbrainzngs")
except Exception as e:
    print(f"   ❌ MusicBrainz API test failed: {e}")

print("\n" + "="*50)
print("✅ API Connection Tests Complete!")
print("="*50)
print("\nNext steps:")
print("1. If any tests failed, follow the error messages above")
print("2. See docs/guides/api_setup.md for detailed setup instructions")
print("3. Once all tests pass, proceed to Phase 4 Step 2: YouTube Search Integration")
print("\n")
