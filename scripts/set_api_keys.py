"""Set API keys in Windows keyring for NEXUS Music Manager."""

import keyring

SERVICE = "nexus_music"

keys = {
    "youtube_api_key": "AIzaSyC0gsFQXUeoAOwkE9s6fjER0U5Ghw1nhPc",
    "spotify_client_id": "31f85987f0cb4a27953df00640de909e",
    "spotify_client_secret": "ded75fefefbe4b8ca80bce9ce249a918",
    "genius_access_token": "aLwoUMtSJ9aj11zDNh7i6nOm3rilv6Q4NiOwtQGnOn8d50lufpZg2vuYE1fdDzXc",
    "acoustid_api_key": "HiexVIyo6u",
}

for key, value in keys.items():
    keyring.set_password(SERVICE, key, value)
    stored = keyring.get_password(SERVICE, key)
    status = "OK" if stored == value else "FAILED"
    print(f"  {key}: {status}")

print("\nAll keys saved to Windows keyring.")
print("Restart the app to pick them up.")
