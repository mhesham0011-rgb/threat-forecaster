import json
from pathlib import Path
from django.utils.timezone import now

from .models import Tactic, Technique, TechniqueStat


def load_attack_from_file(path: str) -> dict:
    """
    For now, read ATT&CK JSON from a local file.
    Later, you can fetch from MITRE's GitHub and cache it.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sync_attack_from_json(data: dict):
    """
    Expecting MITRE-like JSON structure (you'll adapt this to the actual schema).
    Pseudocode-ish but close enough for real use once you map fields correctly.
    """

    # 1) Sync tactics
    tactics_map = {}
    for t in data.get("tactics", []):
        tactic_obj, _ = Tactic.objects.update_or_create(
            attack_id=t["id"],
            defaults={
                "name": t["name"],
                "description": t.get("description", ""),
                "order": t.get("order", 0),
            },
        )
        tactics_map[t["id"]] = tactic_obj

    # 2) Sync techniques
    for tech in data.get("techniques", []):
        tactic_id = tech.get("tactic_id")
        tactic_obj = tactics_map.get(tactic_id)
        if not tactic_obj:
            continue

        technique_obj, _ = Technique.objects.update_or_create(
            attack_id=tech["id"],
            defaults={
                "name": tech["name"],
                "description": tech.get("description", ""),
                "tactic": tactic_obj,
                "mitre_url": tech.get("url", ""),
                "platforms": tech.get("platforms", []),
                "is_deprecated": tech.get("deprecated", False),
            },
        )

        # Ensure a stats row exists
        TechniqueStat.objects.get_or_create(technique=technique_obj)
