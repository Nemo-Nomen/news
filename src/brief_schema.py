"""Delad kontrakt-logik för brevets datastruktur (se config/brief_schema.md).
Används av Fas 6 (skriver riktiga brev) och kan återanvändas av sidan/
Supabase-synk senare.
"""

import hashlib

CATEGORIES = ["jobb", "ekonomi", "politik", "noje", "ai", "skvaller"]


def make_id(link: str) -> str:
    """Deterministiskt ID från länken - samma länk ger alltid samma id,
    ingen state behövs. Används för att koppla betyg till en artikel
    även om den dyker upp igen en annan vecka."""
    return hashlib.sha256(link.encode("utf-8")).hexdigest()[:12]


def empty_brief(generated_at: str) -> dict:
    return {"genererad": generated_at, "kategorier": {cat: [] for cat in CATEGORIES}}
