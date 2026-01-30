"""
Hungarian Proper Nouns Dictionary for Buddhist Terms

This module defines which Buddhist terms should remain capitalized
in Hungarian text when converting from English title case to Hungarian sentence case.

Rules:
1. Proper names of Buddhist figures are always capitalized
2. Sanskrit/Pali terms that are proper nouns remain capitalized
3. "The Three Jewels" (Buddha, Dharma, Sangha) are capitalized when referring to the formal concept
4. School and lineage names are capitalized
5. Common nouns (even of Sanskrit origin) are lowercased in Hungarian
"""

# Buddhist figures - always capitalized
BUDDHIST_FIGURES = {
    'Buddha',
    'Tārā',
    'Tara',
    'Sitatārā',  # White Tārā
    'Syamatārā',  # Green Tārā
    'Mahākāla',
    'Mahakala',
    'Avalokiteśvara',
    'Avalokiteshvara',  # Variant spelling
    'Chenrezig',  # Tibetan name
    'Padmasambhava',
    'Guru',  # As in Guru Rinpoche, Guru Yoga
    'Rinpoche',  # Tibetan title (precious one)
    'Lama',  # Tibetan teacher title
    'Vajradhara',
    'Vajrasattva',
    'Amitābha',
    'Amitabha',
    'Amitāyus',
    'Amitayus',
    'Vairocana',
    'Milarepa',
    'Marpa',
    'Kalu',  # As in Kalu Rinpoche
    'Bodhisattva',  # When referring to a specific being
}

# The Three Jewels - capitalized in formal context
THREE_JEWELS = {
    'Buddha',  # Already in BUDDHIST_FIGURES
    'Dharma',
    'Sangha',
    'Saṅgha',
}

# Three Kāyas - capitalized when referring to specific kāya
KAYAS = {
    'Trikāya',
    'Dharmakāya',
    'Saṃbhogakāya',
    'Sambhogakāya',
    'Nirmāṇakāya',
    'Nirmanakāya',
}

# Buddhist schools and lineages
SCHOOLS_LINEAGES = {
    'Mahāyāna',
    'Mahayana',
    'Vajrayāna',
    'Vajrayana',
    'Theravāda',
    'Theravada',
    'Hīnayāna',  # Historical term
    'Hinayana',
    'Kagyü',
    'Kagyu',
    'Nyingma',
    'Gelug',
    'Sakya',
    'Zen',
    'Ch\'an',
    'Chan',
    'Buddhism',  # Religion name
}

# Acronyms and abbreviations - always uppercase
ACRONYMS = {
    'IAST',  # International Alphabet of Sanskrit Transliteration
}

# Major practices (when used as proper nouns)
PRACTICES = {
    'Ngöndro',
    'Ngondro',
    'Mahāmudrā',
    'Mahamudra',
    'Dzogchen',
    'Vipassanā',
    'Vipassana',
    'Shamatha',
    'Śamatha',
    'Samatha',
    'Shikantaza',
}

# Intermediate states
BARDOS = {
    'Bardo',
}

# Pāramitās - lowercase in general usage but check context
# "a hat pāramitā" (lowercase) vs "Prajñāpāramitā" (title)
PARAMITAS = {
    'Prajñāpāramitā',
    'Prajnaparamita',
}

# Combine all proper nouns
PROPER_NOUNS = (
    BUDDHIST_FIGURES |
    THREE_JEWELS |
    KAYAS |
    SCHOOLS_LINEAGES |
    PRACTICES |
    BARDOS |
    PARAMITAS |
    ACRONYMS
)

# Terms that might look like proper nouns but are common nouns in Hungarian
# These should be LOWERCASED (except when they start a sentence)
COMMON_NOUNS = {
    'kāya',  # "a három kāya" (the three bodies)
    'kaya',
    'pāramitā',  # "a hat pāramitā" (the six perfections)
    'paramita',
    'ékszer',  # "három ékszer" (three jewels - common reference)
    'yāna',  # "a három yāna" (the three vehicles)
    'yana',
    'tantra',
    'mantra',
    'mudrā',
    'mudra',
    'sūtra',
    'sutra',
    'maṇḍala',
    'mandala',
}

# Special multi-word proper nouns
MULTI_WORD_PROPER_NOUNS = {
    'Guru Rinpoche',
    'Kalu Rinpoche',
}

def is_proper_noun(word):
    """
    Check if a word should be capitalized as a proper noun.

    Args:
        word: The word to check (may include punctuation)

    Returns:
        bool: True if the word is a proper noun
    """
    # Strip common punctuation for checking
    clean_word = word.strip('.,;:!?"\'()[]–—')

    # Check direct match
    if clean_word in PROPER_NOUNS:
        return True

    # Check without diacritics (basic ASCII version)
    ascii_word = remove_diacritics(clean_word)
    for proper_noun in PROPER_NOUNS:
        if remove_diacritics(proper_noun) == ascii_word:
            return True

    return False

def is_common_noun(word):
    """
    Check if a word is explicitly a common noun that should be lowercased.

    Args:
        word: The word to check

    Returns:
        bool: True if the word should be lowercased
    """
    clean_word = word.strip('.,;:!?"\'()[]–—').lower()
    return clean_word in COMMON_NOUNS

def remove_diacritics(text):
    """
    Remove diacritical marks for comparison.

    This helps match words like 'Tara' and 'Tārā'.
    """
    import unicodedata
    # Normalize to NFD (decomposed form) then filter out combining marks
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

def has_sanskrit_diacritics(word):
    """
    Check if a word contains Sanskrit diacritical marks.

    Sanskrit diacritics include: ā, ī, ū, ṃ, ḥ, ṇ, ṭ, ḍ, ś, ṣ, etc.
    """
    sanskrit_marks = set('āīūṛṝḷḹṃḥṅñṭḍṇśṣ')
    return any(char in sanskrit_marks for char in word.lower())

if __name__ == '__main__':
    # Test cases
    test_words = [
        'Buddha',
        'Dharma',
        'kāya',
        'Dharmakāya',
        'Tārā',
        'pāramitā',
        'Prajñāpāramitā',
        'Mahāyāna',
        'ékszer',
    ]

    print("Proper Noun Tests:")
    for word in test_words:
        print(f"  {word:20} -> {'PROPER NOUN' if is_proper_noun(word) else 'common noun'}")
