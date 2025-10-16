import json
from typing import Iterable, Tuple, Optional
from django.db import transaction

from apps.taxonomy.models import ATTCKTechnique


def _extract_external_id(obj: dict) -> Optional[str]:
    """
    ATT&CK technique ID comes from external_references[].external_id, e.g. 'T1059'.
    """
    for ref in obj.get("external_references", []) or []:
        ext_id = ref.get("external_id")
        # Heuristic: ATT&CK technique IDs start with 'T' (Txxxx).
        if ext_id and isinstance(ext_id, str) and ext_id.startswith("T"):
            return ext_id
    return None


def _extract_name(obj: dict) -> str:
    return obj.get("name", "").strip()


def _extract_tactics(obj: dict) -> Iterable[str]:
    """
    Tactics appear in kill_chain_phases[].phase_name where kill_chain_name == 'mitre-attack'.
    There may be multiple tactics; we return a generator of strings (lowercased).
    """
    for phase in obj.get("kill_chain_phases", []) or []:
        if phase.get("kill_chain_name") == "mitre-attack":
            name = (phase.get("phase_name") or "").strip().lower()
            if name:
                yield name


def _choose_primary_tactic(tactics: Iterable[str]) -> str:
    """
    Your current model stores a single 'tactic' (CharField).
    We pick a stable, deterministic one if there are multiple:
      - Prefer 'execution' if present (common for many techniques).
      - Else pick the first in sorted order.
      - Else 'unknown'.
    """
    tset = {t for t in tactics if t}
    if not tset:
        return "unknown"
    if "execution" in tset:
        return "execution"
    return sorted(tset)[0]


@transaction.atomic
def load_attack_from_dict(stix_bundle: dict) -> Tuple[int, int]:
    """
    Insert/update ATT&CK techniques from a parsed STIX 2.1 bundle dict.

    Returns:
        (created_count, updated_count)
    """
    created = 0
    updated = 0

    objects = stix_bundle.get("objects", [])
    for obj in objects:
        # Techniques are STIX type 'attack-pattern'
        if obj.get("type") != "attack-pattern":
            continue

        tid = _extract_external_id(obj)
        if not tid:
            continue  # skip non-technique objects or those without external_id

        name = _extract_name(obj)
        tactic = _choose_primary_tactic(_extract_tactics(obj))

        # Upsert by tid
        inst, is_created = ATTCKTechnique.objects.update_or_create(
            tid=tid,
            defaults={"name": name, "tactic": tactic},
        )
        if is_created:
            created += 1
        else:
            updated += 1

    return created, updated


def load_attack_from_file(path: str) -> Tuple[int, int]:
    """
    Load ATT&CK techniques from a local JSON file.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return load_attack_from_dict(data)
