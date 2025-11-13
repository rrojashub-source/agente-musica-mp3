# API Setup Guide - Phase 4

**Created:** November 12, 2025
**Phase:** 4 - Search & Download System
**Purpose:** Setup YouTube, Spotify, and MusicBrainz API credentials

---

## 🎯 Overview

Phase 4 requires 3 API integrations:
1. **YouTube Data API v3** - Search and download videos
2. **Spotify Web API** - Search tracks/albums/artists metadata
3. **MusicBrainz API** - Auto-complete metadata (no credentials needed)

**Total time:** ~20 minutes
**Cost:** FREE (all APIs have free tiers)

---

## 📋 Prerequisites

Before starting:
- ✅ Google account (for YouTube API)
- ✅ Spotify account (for Spotify API)
- ✅ Internet connection
- ✅ Access to `~/.claude/secrets/credentials.json`

---

## 1️⃣ YouTube Data API v3 Setup

### **Step 1: Create Google Cloud Project**

1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. Click **"Select a project"** → **"NEW PROJECT"**
4. Project name: `NEXUS_Music_Manager` (or your preference)
5. Click **"CREATE"**
6. Wait ~30 seconds for project creation

---

### **Step 2: Enable YouTube Data API v3**

1. With your new project selected, go to:
   https://console.cloud.google.com/apis/library
2. Search: `YouTube Data API v3`
3. Click on **"YouTube Data API v3"**
4. Click **"ENABLE"**
5. Wait ~10 seconds for activation

---

### **Step 3: Create API Credentials**

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"CREATE CREDENTIALS"** → **"API key"**
3. A popup shows your API key (looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
4. **COPY THIS KEY** (you'll need it in Step 4)
5. (Optional) Click **"RESTRICT KEY"**:
   - API restrictions: Select **"YouTube Data API v3"**
   - This improves security
   - Click **"SAVE"**

---

### **Step 4: Store API Key Securely**

Run this command (replace `YOUR_API_KEY` with the key you copied):

```bash
bash ~/.claude/secrets/set-secret.sh apis youtube api_key "YOUR_API_KEY"
```

**Example:**
```bash
bash ~/.claude/secrets/set-secret.sh apis youtube api_key "AIzaSyABCDEF1234567890XXXXXXXXXXXXX"
```

**Expected output:**
```
Secret set successfully: apis.youtube.api_key
Backup created: ~/.claude/secrets/credentials.json.backup
Backup synced to Z:\NEXUS_SECRETS_BACKUP\
```

---

### **Step 5: Test YouTube API**

Verify your API key works:

```bash
curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key=$(bash ~/.claude/secrets/get-secret.sh apis youtube api_key)"
```

**Expected:** JSON response with search results

**If error:** Check your API key is correct and YouTube API is enabled

---

### **📊 YouTube API Limits**

- **Free quota:** 10,000 requests/day
- **Cost per search:** ~100 units
- **Searches per day:** ~100 searches
- **Reset:** Daily at midnight Pacific Time

**Good for:** Personal use, testing, prototyping
**Not enough for:** Production app with 1000+ users

---

## 2️⃣ Spotify Web API Setup

### **Step 1: Create Spotify App**

1. Go to: https://developer.spotify.com/dashboard
2. Sign in with your Spotify account (free or premium)
3. Click **"Create app"**
4. Fill form:
   - **App name:** `NEXUS Music Manager`
   - **App description:** `Personal music library manager`
   - **Redirect URI:** `http://localhost:8888/callback`
   - **Which API/SDKs:** Check **Web API**
5. Agree to terms
6. Click **"SAVE"**

---

### **Step 2: Get Client ID & Client Secret**

1. In your app dashboard, click **"Settings"**
2. You'll see:
   - **Client ID:** (looks like `a1b2c3d4e5f6g7h8i9j0`)
   - **Client Secret:** Click **"View client secret"** (looks like `z9y8x7w6v5u4t3s2r1q0`)
3. **COPY BOTH** (you'll need them in Step 3)

---

### **Step 3: Store Credentials Securely**

Run these commands (replace with your actual values):

```bash
# Store Client ID
bash ~/.claude/secrets/set-secret.sh apis spotify client_id "YOUR_CLIENT_ID"

# Store Client Secret
bash ~/.claude/secrets/set-secret.sh apis spotify client_secret "YOUR_CLIENT_SECRET"
```

**Example:**
```bash
bash ~/.claude/secrets/set-secret.sh apis spotify client_id "a1b2c3d4e5f6g7h8i9j0"
bash ~/.claude/secrets/set-secret.sh apis spotify client_secret "z9y8x7w6v5u4t3s2r1q0"
```

---

### **Step 4: Test Spotify API**

We'll test this with Python code in the next step (requires `spotipy` library).

---

### **📊 Spotify API Limits**

- **Free quota:** 100 requests/second
- **Daily limit:** None (unlimited)
- **Rate limit:** 429 error if exceeded (automatic retry)

**Good for:** Personal and commercial use
**Restrictions:** Cannot download music from Spotify (DRM protected)

---

## 3️⃣ MusicBrainz API Setup

### **No API Key Needed! ✅**

MusicBrainz is completely free and doesn't require registration.

**Only requirement:** Set a user agent to identify your app.

**We'll set this in code:**
```python
import musicbrainzngs as mb
mb.set_useragent("NexusMusicManager", "1.0", "https://github.com/yourusername/nexus")
```

**That's it!** No credentials needed.

---

### **📊 MusicBrainz API Limits**

- **Free quota:** Unlimited
- **Rate limit:** 1 request/second (polite usage)
- **Cost:** FREE forever

**Good for:** All use cases (personal and commercial)
**Best for:** Metadata auto-completion

---

## ✅ Verification Checklist

After completing all steps, verify:

```bash
# 1. Check YouTube API key stored
bash ~/.claude/secrets/get-secret.sh apis youtube api_key
# Expected: AIzaSy... (last 4 chars shown)

# 2. Check Spotify credentials stored
bash ~/.claude/secrets/get-secret.sh apis spotify client_id
bash ~/.claude/secrets/get-secret.sh apis spotify client_secret
# Expected: Client ID and secret (last 4 chars shown)

# 3. List all API secrets
bash ~/.claude/secrets/list-secrets.sh
# Expected: See "apis" category with youtube and spotify
```

---

## 🔧 Test Connection Script

Create this test script to verify all APIs work:

**File:** `scripts/test_apis.py`

```python
#!/usr/bin/env python3
"""
Test API connections for Phase 4
Run: python scripts/test_apis.py
"""
import json
from pathlib import Path
import requests

# Load credentials
secrets_path = Path.home() / ".claude" / "secrets" / "credentials.json"
with open(secrets_path) as f:
    secrets = json.load(f)

print("🧪 Testing API Connections...\n")

# Test 1: YouTube API
print("1️⃣ Testing YouTube Data API v3...")
youtube_key = secrets['apis']['youtube']['api_key']
response = requests.get(
    "https://www.googleapis.com/youtube/v3/search",
    params={'part': 'snippet', 'q': 'test', 'key': youtube_key}
)
if response.status_code == 200:
    print("   ✅ YouTube API: Connected")
else:
    print(f"   ❌ YouTube API: Failed ({response.status_code})")

# Test 2: Spotify API
print("\n2️⃣ Testing Spotify Web API...")
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    client_id = secrets['apis']['spotify']['client_id']
    client_secret = secrets['apis']['spotify']['client_secret']

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    ))

    results = sp.search(q='test', limit=1)
    print("   ✅ Spotify API: Connected")
except Exception as e:
    print(f"   ❌ Spotify API: Failed ({e})")

# Test 3: MusicBrainz API
print("\n3️⃣ Testing MusicBrainz API...")
try:
    import musicbrainzngs as mb
    mb.set_useragent("NexusMusicManager", "1.0")
    result = mb.search_recordings(query="test", limit=1)
    print("   ✅ MusicBrainz API: Connected")
except Exception as e:
    print(f"   ❌ MusicBrainz API: Failed ({e})")

print("\n✅ All API tests complete!")
```

**Run:**
```bash
python scripts/test_apis.py
```

**Expected output:**
```
🧪 Testing API Connections...

1️⃣ Testing YouTube Data API v3...
   ✅ YouTube API: Connected

2️⃣ Testing Spotify Web API...
   ✅ Spotify API: Connected

3️⃣ Testing MusicBrainz API...
   ✅ MusicBrainz API: Connected

✅ All API tests complete!
```

---

## 🚨 Troubleshooting

### **YouTube API Issues:**

**Error: "API key not valid"**
- Solution: Check key is correct, API is enabled in Google Cloud Console

**Error: "Daily quota exceeded"**
- Solution: Wait until midnight Pacific Time for quota reset
- Alternative: Create new Google Cloud project with new API key

**Error: "Access Not Configured"**
- Solution: Enable YouTube Data API v3 in Google Cloud Console

---

### **Spotify API Issues:**

**Error: "Invalid client"**
- Solution: Check Client ID and Secret are correct
- Solution: Check app is not in Development Mode restrictions

**Error: "Rate limit exceeded"**
- Solution: Add delay between requests (automatic in spotipy)

---

### **MusicBrainz API Issues:**

**Error: "Connection refused"**
- Solution: Check internet connection
- Solution: MusicBrainz may be down (check https://musicbrainz.org/)

**Error: "Rate limit exceeded"**
- Solution: Add 1 second delay between requests

---

## 📦 Required Python Packages

Add to `requirements.txt`:

```
google-api-python-client==2.100.0
spotipy==2.23.0
musicbrainzngs==0.7.1
```

**Install:**
```bash
pip install -r requirements.txt
```

---

## 🔐 Security Best Practices

1. **Never commit API keys to Git**
   - ✅ Keys stored in `~/.claude/secrets/credentials.json` (not in repo)
   - ✅ `.gitignore` already excludes secrets

2. **Restrict API keys**
   - YouTube: Restrict to YouTube Data API v3 only
   - Spotify: Restrict to Web API only

3. **Rotate keys regularly**
   - Recommendation: Every 3-6 months
   - Or immediately if compromised

4. **Monitor usage**
   - YouTube: Check quota usage in Google Cloud Console
   - Spotify: Check usage in Spotify Developer Dashboard

---

## ✅ Completion Criteria

**Phase 4 Step 1 is COMPLETE when:**

1. ✅ YouTube API key stored in secrets
2. ✅ Spotify Client ID + Secret stored in secrets
3. ✅ Test script runs successfully (all 3 APIs connected)
4. ✅ Required packages installed (`requirements.txt`)

---

**Next Step:** Phase 4 Step 2 - YouTube Search Integration (TDD)

---

**Created by:** NEXUS@CLI
**Last Updated:** November 12, 2025
**Maintained by:** Ricardo + NEXUS
