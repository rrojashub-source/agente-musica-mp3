"""
Lyrics Analyzer - Tier 2 content classification using lyrics

Fetches lyrics from Genius/Musixmatch and analyzes for explicit content.

Dependencies:
    pip install lyricsgenius better-profanity

Created: December 8, 2025
"""

import logging
import re
from typing import Optional, List
from pathlib import Path

from .classifier import ContentScore

logger = logging.getLogger(__name__)


# Profanity word lists (Spanish + English)
PROFANITY_ES = {
    # Strong (weight 1.0)
    'puta', 'puto', 'mierda', 'coño', 'carajo', 'verga', 'pinga',
    'cabron', 'cabrón', 'pendejo', 'pendeja', 'joder', 'cojones',
    'culo', 'perra', 'perro', 'marica', 'maricón', 'maricon',
    'malparido', 'hijueputa', 'gonorrea', 'chimba',
    # Medium (weight 0.5)
    'cagar', 'cagada', 'chingar', 'chingada', 'mamada', 'mamón',
    'huevon', 'huevón', 'culero', 'pinche', 'fregada',
}

PROFANITY_EN = {
    # Strong (weight 1.0)
    'fuck', 'fucking', 'fucked', 'fucker', 'motherfucker', 'mf',
    'shit', 'shitty', 'bullshit', 'bitch', 'bitches', 'asshole',
    'ass', 'damn', 'cunt', 'dick', 'cock', 'pussy', 'whore',
    'slut', 'bastard', 'nigga', 'nigger',
    # Medium (weight 0.5)
    'hell', 'crap', 'piss', 'suck', 'sucks', 'wtf', 'stfu',
}

VIOLENCE_KEYWORDS = {
    'kill', 'murder', 'matar', 'muerte', 'dead', 'muerto',
    'gun', 'pistola', 'shoot', 'disparo', 'blood', 'sangre',
    'fight', 'pelea', 'war', 'guerra', 'knife', 'cuchillo',
    'beat', 'golpear', 'hit', 'punch', 'stab', 'apuñalar',
}

DRUG_KEYWORDS = {
    'cocaine', 'cocaina', 'crack', 'heroin', 'heroina',
    'meth', 'weed', 'marijuana', 'marihuana', 'hierba',
    'pills', 'pastillas', 'lean', 'codeine', 'codeina',
    'molly', 'ecstasy', 'extasis', 'droga', 'drugs',
    'smoke', 'fumar', 'high', 'drogado', 'perico',
    'blunt', 'joint', 'porro', 'cannabis', 'thc',
}

SEXUAL_KEYWORDS = {
    'sex', 'sexo', 'sexy', 'naked', 'desnudo', 'nude',
    'porn', 'porno', 'strip', 'stripper', 'twerk',
    'orgasm', 'orgasmo', 'horny', 'caliente', 'cachondo',
    'booty', 'nalga', 'titties', 'tetas', 'breasts',
    'penetrar', 'penetrate', 'ride', 'montar',
}

POSITIVE_KEYWORDS = {
    'love', 'amor', 'happy', 'feliz', 'joy', 'alegria',
    'peace', 'paz', 'hope', 'esperanza', 'dream', 'sueño',
    'smile', 'sonrisa', 'friend', 'amigo', 'family', 'familia',
    'beautiful', 'hermoso', 'wonderful', 'maravilloso',
    'thank', 'gracias', 'bless', 'bendicion',
}


class LyricsAnalyzer:
    """
    Analyzes song lyrics for content classification
    """

    def __init__(self):
        self._genius = None
        self._profanity_checker = None
        self._init_genius()
        self._init_profanity()

    def _init_genius(self):
        """Initialize Genius API client"""
        try:
            import lyricsgenius
            # Try to get API token from multiple sources
            import os
            token = None

            # 1. Try environment variable
            token = os.environ.get('GENIUS_ACCESS_TOKEN')

            # 2. Try keyring (like other API keys in the app)
            if not token:
                try:
                    import keyring
                    token = keyring.get_password("nexus_music", "genius_token")
                except Exception:
                    pass

            # 3. Try credentials.json
            if not token:
                try:
                    from pathlib import Path
                    import json
                    creds_path = Path.home() / ".claude" / "secrets" / "credentials.json"
                    if creds_path.exists():
                        with open(creds_path) as f:
                            creds = json.load(f)
                        token = creds.get('apis', {}).get('genius', {}).get('api_key')
                except Exception:
                    pass

            if token:
                self._genius = lyricsgenius.Genius(token, verbose=False, timeout=10)
                self._genius.remove_section_headers = True
                logger.info("Genius API initialized")
            else:
                logger.warning("GENIUS_ACCESS_TOKEN not set, lyrics analysis limited")
                logger.info("Set token via: keyring or GENIUS_ACCESS_TOKEN env var")
        except ImportError:
            logger.warning("lyricsgenius not installed: pip install lyricsgenius")

    def _init_profanity(self):
        """Initialize profanity checker"""
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            self._profanity_checker = profanity
            logger.info("Profanity checker initialized")
        except ImportError:
            logger.warning("better-profanity not installed: pip install better-profanity")

    def analyze(self, artist: str, title: str) -> Optional[ContentScore]:
        """
        Analyze lyrics for content

        Args:
            artist: Artist name
            title: Song title

        Returns:
            ContentScore or None if lyrics not found
        """
        lyrics = self._fetch_lyrics(artist, title)

        if not lyrics:
            return None

        return self._analyze_lyrics_content(lyrics)

    def _fetch_lyrics(self, artist: str, title: str) -> Optional[str]:
        """Fetch lyrics from Genius API"""
        if not self._genius:
            return None

        try:
            # Search for song
            song = self._genius.search_song(title, artist)

            if song and song.lyrics:
                # Clean up lyrics
                lyrics = song.lyrics

                # Remove common Genius artifacts
                lyrics = re.sub(r'\[.*?\]', '', lyrics)  # Remove [Verse 1], etc.
                lyrics = re.sub(r'^\d+\s*Embed.*$', '', lyrics, flags=re.MULTILINE)
                lyrics = re.sub(r'See .* LiveGet tickets.*$', '', lyrics, flags=re.MULTILINE)
                lyrics = lyrics.strip()

                logger.debug(f"Found lyrics for {artist} - {title} ({len(lyrics)} chars)")
                return lyrics
        except Exception as e:
            logger.debug(f"Could not fetch lyrics for {artist} - {title}: {e}")

        return None

    def _analyze_lyrics_content(self, lyrics: str) -> ContentScore:
        """
        Analyze lyrics text for content

        Returns ContentScore with detailed breakdown
        """
        score = ContentScore(source="lyrics")
        lyrics_lower = lyrics.lower()
        words = re.findall(r'\b\w+\b', lyrics_lower)
        word_count = len(words)

        if word_count == 0:
            score.confidence = 0.1
            return score

        # Count profanity
        profanity_count = 0
        for word in words:
            if word in PROFANITY_ES or word in PROFANITY_EN:
                profanity_count += 1

        # Check with better_profanity if available
        if self._profanity_checker:
            try:
                if self._profanity_checker.contains_profanity(lyrics):
                    profanity_count = max(profanity_count, 1)
            except:
                pass

        # Calculate profanity density (profanity per 100 words)
        profanity_density = (profanity_count / word_count) * 100 if word_count > 0 else 0

        # Score based on density
        if profanity_density > 5:
            score.profanity = 1.0
        elif profanity_density > 2:
            score.profanity = 0.8
        elif profanity_density > 1:
            score.profanity = 0.6
        elif profanity_density > 0.5:
            score.profanity = 0.4
        elif profanity_count > 0:
            score.profanity = 0.2

        # Count violence keywords
        violence_count = sum(1 for word in words if word in VIOLENCE_KEYWORDS)
        violence_density = (violence_count / word_count) * 100
        if violence_density > 2:
            score.violence = 0.8
        elif violence_density > 0.5:
            score.violence = 0.5
        elif violence_count > 0:
            score.violence = 0.2

        # Count drug references
        drug_count = sum(1 for word in words if word in DRUG_KEYWORDS)
        drug_density = (drug_count / word_count) * 100
        if drug_density > 2:
            score.substance = 0.9
        elif drug_density > 0.5:
            score.substance = 0.6
        elif drug_count > 0:
            score.substance = 0.3

        # Count sexual content
        sexual_count = sum(1 for word in words if word in SEXUAL_KEYWORDS)
        sexual_density = (sexual_count / word_count) * 100
        if sexual_density > 3:
            score.sexual_content = 0.9
        elif sexual_density > 1:
            score.sexual_content = 0.6
        elif sexual_count > 0:
            score.sexual_content = 0.3

        # Count positive messages
        positive_count = sum(1 for word in words if word in POSITIVE_KEYWORDS)
        positive_density = (positive_count / word_count) * 100
        if positive_density > 3:
            score.positive_messages = 0.9
        elif positive_density > 1:
            score.positive_messages = 0.6
        elif positive_count > 0:
            score.positive_messages = 0.3

        # Calculate overall explicit score
        score.explicit_score = max(
            score.profanity * 0.4,
            score.violence * 0.2,
            score.substance * 0.2,
            score.sexual_content * 0.2,
        )

        # Adjust for context
        if score.profanity > 0.6 or score.sexual_content > 0.6:
            score.explicit_score = max(score.explicit_score, 0.7)

        # Clean score (inverse of explicit, modified by positive)
        score.clean_score = max(0, 1 - score.explicit_score) * (1 + score.positive_messages * 0.2)
        score.clean_score = min(1.0, score.clean_score)

        # Confidence based on analysis depth
        score.confidence = 0.85  # Lyrics analysis is quite reliable

        # Add reasons
        if profanity_count > 0:
            score.reasons.append(f"Profanity detected: {profanity_count} instances ({profanity_density:.1f}%)")
        if violence_count > 0:
            score.reasons.append(f"Violence references: {violence_count}")
        if drug_count > 0:
            score.reasons.append(f"Drug references: {drug_count}")
        if sexual_count > 0:
            score.reasons.append(f"Sexual content: {sexual_count}")
        if positive_count > 0:
            score.reasons.append(f"Positive messages: {positive_count}")
        if not score.reasons:
            score.reasons.append("No explicit content detected in lyrics")

        return score

    def analyze_text(self, lyrics: str) -> ContentScore:
        """
        Analyze provided lyrics text directly

        Args:
            lyrics: Raw lyrics text

        Returns:
            ContentScore
        """
        return self._analyze_lyrics_content(lyrics)
