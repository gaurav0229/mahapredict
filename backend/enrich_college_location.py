"""
Best-effort city/district enrichment for the colleges table.

The official CAP cutoff/seat-matrix PDFs (extract_cap_data.py) don't include
college addresses at all - only institute code and name. But most institute
names follow the Indian convention "<trust/org>'s <College Name>, <Location>"
where <Location> is a taluka, city, or district name. This script:

  1. Matches each of Maharashtra's 36 official districts (plus recent renames:
     Aurangabad->Chhatrapati Sambhajinagar, Osmanabad->Dharashiv,
     Ahmednagar->Ahilyanagar) directly against college names.
  2. For names that don't mention a district directly, falls back to a
     taluka->district lookup (talukas sourced from Wikipedia's "List of
     talukas of Maharashtra", checked 2026-09) - a taluka name determines
     its parent district unambiguously *except* for a handful of taluka
     names that recur across multiple districts, which are deliberately
     excluded from the fallback list below to avoid a wrong guess.

In both passes, when multiple location names appear in one string (e.g. an
org name mentioning one place and the actual location being another), the
RIGHTMOST match wins - Indian institute names conventionally put the actual
location last ("<College>, <Location>"), while earlier mentions are usually
part of a trust/road/highway name.

This is explicitly approximate, unlike the CAP cutoff data (which is
authoritative). Colleges where no confident match is found are left with
district=NULL rather than guessed - district is treated as informational,
not used for hard filtering, precisely because of this.

Usage: .venv/Scripts/python.exe enrich_college_location.py [--apply]
Without --apply, only prints what would change (dry run).
"""

from __future__ import annotations

import argparse
import re
from collections import Counter

from database import SessionLocal
from models import College

DISTRICT_ALIASES: dict[str, list[str]] = {
    "Ahmednagar": ["Ahmednagar", "Ahilyanagar"],
    "Akola": ["Akola"],
    "Amravati": ["Amravati", "Amaravati"],
    "Chhatrapati Sambhajinagar": ["Aurangabad", "Chhatrapati Sambhajinagar", "Sambhajinagar"],
    "Beed": ["Beed"],
    "Bhandara": ["Bhandara"],
    "Buldhana": ["Buldhana", "Buldana"],
    "Chandrapur": ["Chandrapur"],
    "Dhule": ["Dhule", "Dhulia"],
    "Gadchiroli": ["Gadchiroli"],
    "Gondia": ["Gondia"],
    "Hingoli": ["Hingoli"],
    "Jalgaon": ["Jalgaon"],
    "Jalna": ["Jalna"],
    "Kolhapur": ["Kolhapur"],
    "Latur": ["Latur"],
    "Mumbai": ["Mumbai", "Bombay", "Navi Mumbai"],
    "Nagpur": ["Nagpur"],
    "Nanded": ["Nanded"],
    "Nandurbar": ["Nandurbar"],
    "Nashik": ["Nashik", "Nasik"],
    "Dharashiv": ["Osmanabad", "Dharashiv"],
    "Palghar": ["Palghar"],
    "Parbhani": ["Parbhani"],
    "Pune": ["Pune", "Poona"],
    "Raigad": ["Raigad"],
    "Ratnagiri": ["Ratnagiri"],
    "Sangli": ["Sangli"],
    "Satara": ["Satara"],
    "Sindhudurg": ["Sindhudurg"],
    "Solapur": ["Solapur", "Sholapur"],
    "Thane": ["Thane"],
    "Wardha": ["Wardha"],
    "Washim": ["Washim"],
    "Yavatmal": ["Yavatmal", "Yeotmal"],
}

# Source: https://en.wikipedia.org/wiki/List_of_talukas_of_Maharashtra (checked 2026-09).
# Short/very common words that also appear as ordinary English/Marathi words in
# institute names ("Nagar", "City" etc.) are deliberately omitted to avoid false
# positives, same lesson as the district-alias pass.
TALUKAS_BY_DISTRICT: dict[str, list[str]] = {
    "Sindhudurg": ["Kankavli", "Vaibhavwadi", "Devgad", "Malwan", "Sawantwadi", "Kudal", "Vengurla", "Dodamarg"],
    "Ratnagiri": ["Ratnagiri", "Sangameshwar", "Lanja", "Rajapur", "Chiplun", "Guhagar", "Dapoli", "Mandangad", "Khed"],
    "Raigad": ["Pen", "Alibag", "Murud", "Panvel", "Uran", "Karjat", "Khalapur", "Mangaon", "Tala", "Roha", "Sudhagad", "Mahad", "Poladpur", "Shrivardhan", "Mhasala"],
    "Thane": ["Kalyan", "Murbad", "Shahapur", "Bhiwandi", "Ulhasnagar", "Ambarnath"],
    "Palghar": ["Vasai", "Dahanu", "Talasari", "Jawhar", "Mokhada", "Vada", "Vikramgad", "Boisar"],
    "Nashik": ["Igatpuri", "Dindori", "Trimbakeshwar", "Kalwan", "Deola", "Surgana", "Baglan", "Malegaon", "Nandgaon", "Chandwad", "Niphad", "Sinnar", "Yeola"],
    "Nandurbar": ["Navapur", "Shahada", "Talode", "Akkalkuwa"],
    "Dhule": ["Sakri", "Sindkheda", "Shirpur"],
    "Jalgaon": ["Jamner", "Erandol", "Dharangaon", "Bhusawal", "Raver", "Muktainagar", "Bodwad", "Yawal", "Amalner", "Parola", "Chopda", "Pachora", "Bhadgaon", "Chalisgaon"],
    "Buldhana": ["Chikhli", "Jalgaon Jamod", "Sangrampur", "Malkapur", "Motala", "Nandura", "Khamgaon", "Shegaon", "Mehkar", "Sindkhed Raja", "Lonar"],
    "Akola": ["Akot", "Telhara", "Balapur", "Patur", "Murtajapur", "Barshitakli"],
    "Washim": ["Risod", "Mangrulpir", "Karanja Lad", "Manora"],
    "Amravati": ["Bhatkuli", "Dharni", "Chikhaldara", "Achalpur", "Chandurbazar", "Morshi", "Warud", "Daryapur", "Anjangaon"],
    "Wardha": ["Deoli", "Seloo", "Arvi", "Ashti", "Hinganghat", "Samudrapur"],
    "Nagpur": ["Kamptee", "Hingna", "Katol", "Narkhed", "Savner", "Kalameshwar", "Ramtek", "Mouda", "Parseoni", "Umred", "Kuhi", "Bhiwapur"],
    "Bhandara": ["Tumsar", "Pauni", "Mohadi", "Sakoli", "Lakhani", "Lakhandur"],
    "Gondia": ["Goregaon", "Salekasa", "Tiroda", "Deori", "Amgaon", "Arjuni-Morgaon", "Sadak-Arjuni"],
    "Gadchiroli": ["Dhanora", "Chamorshi", "Mulchera", "Desaiganj", "Armori", "Kurkheda", "Korchi", "Aheri", "Etapalli", "Bhamragad", "Sironcha"],
    "Chandrapur": ["Saoli", "Mul", "Ballarpur", "Pombhurna", "Gondpimpri", "Warora", "Chimur", "Bhadravati", "Bramhapuri", "Nagbhid", "Sindewahi", "Rajura", "Korpana", "Jiwati"],
    "Yavatmal": ["Arni", "Babhulgaon", "Kalamb", "Darwha", "Digras", "Ner", "Pusad", "Umarkhed", "Mahagaon", "Kelapur", "Ralegaon", "Ghatanji", "Wani", "Maregaon"],
    "Nanded": ["Ardhapur", "Mudkhed", "Bhokar", "Loha", "Kandhar", "Kinwat", "Himayatnagar", "Hadgaon", "Mahur", "Deglur", "Mukhed", "Dharmabad", "Biloli", "Naigaon"],
    "Hingoli": ["Sengaon", "Kalamnuri", "Basmath", "Aundha Nagnath"],
    "Parbhani": ["Sonpeth", "Gangakhed", "Palam", "Purna", "Sailu", "Jintur", "Manwath", "Pathri"],
    "Jalna": ["Bhokardan", "Jafrabad", "Badnapur", "Partur", "Ambad", "Ghansawangi", "Mantha"],
    "Chhatrapati Sambhajinagar": ["Kannad", "Soegaon", "Sillod", "Phulambri", "Khuldabad", "Vaijapur", "Gangapur", "Paithan"],
    "Beed": ["Georai", "Patoda", "Shirur-Kasar", "Ambejogai", "Majalgaon", "Wadwani", "Kaij", "Dharur", "Parli"],
    "Latur": ["Ausa", "Ahmedpur", "Jalkot", "Chakur", "Nilanga", "Deoni", "Udgir"],
    "Dharashiv": ["Tuljapur", "Bhum", "Paranda", "Washi", "Umarga", "Lohara"],
    "Solapur": ["Barshi", "Akkalkot", "Kurduwadi", "Madha", "Karmala", "Pandharpur", "Mohol", "Malshiras", "Mangalvedhe", "Sangole"],
    "Ahmednagar": ["Shevgaon", "Pathardi", "Parner", "Sangamner", "Kopargaon", "Akole", "Shrirampur", "Nevasa", "Rahata", "Rahuri", "Shrigonda", "Jamkhed"],
    "Pune": ["Haveli", "Junnar", "Ambegaon", "Maval", "Mulshi", "Shirur", "Purandhar", "Velhe", "Bhor", "Baramati", "Indapur", "Daund", "Wagholi", "Lohegaon", "Hinjewadi", "Chinchwad", "Pimpri"],
    "Satara": ["Jaoli", "Koregaon", "Wai", "Mahabaleshwar", "Khandala", "Phaltan", "Khatav", "Karad", "Patan"],
    "Sangli": ["Miraj", "Kavathemahankal", "Tasgaon", "Jat", "Walwa", "Shirala", "Khanapur", "Atpadi", "Palus", "Kadegaon"],
    "Kolhapur": ["Karvir", "Panhala", "Shahuwadi", "Kagal", "Ichalkaranji", "Hatkanangale", "Shirol", "Radhanagari", "Gaganbawada", "Bhudargad", "Gadhinglaj", "Chandgad", "Ajra"],
}


def build_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    conflicts: set[str] = set()
    for source in (DISTRICT_ALIASES, {d: t for d, t in TALUKAS_BY_DISTRICT.items()}):
        for district, aliases in source.items():
            for alias in aliases:
                key = alias.lower()
                if key in index and index[key] != district:
                    conflicts.add(key)
                else:
                    index[key] = district
    for c in conflicts:
        index.pop(c, None)
    if conflicts:
        print(f"Excluded {len(conflicts)} ambiguous alias(es) (appear in >1 district): {sorted(conflicts)}")
    return index


def match_district(name: str, alias_index: dict[str, str]) -> str | None:
    best, best_pos = None, -1
    for alias in sorted(alias_index, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(alias) + r"\b", name, re.IGNORECASE):
            if m.start() > best_pos:
                best_pos, best = m.start(), alias_index[alias]
    return best


def guess_city(name: str) -> str | None:
    """Best-effort only: last comma-separated segment, cleaned up. Not used for
    filtering - district is the reliable dimension here."""
    parts = [p.strip(" .") for p in name.split(",")]
    if len(parts) < 2:
        return None
    last = parts[-1]
    # Drop trailing pin codes / "Tal./Dist." prefixes that sometimes survive
    last = re.sub(r"^(Tal\.?|Dist\.?)\s*", "", last, flags=re.IGNORECASE).strip()
    if not last or last.isdigit() or len(last) < 3:
        return None
    return last


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to the database (default: dry run)")
    args = parser.parse_args()

    alias_index = build_alias_index()
    db = SessionLocal()
    colleges = db.query(College).order_by(College.name).all()

    matched_district = 0
    matched_city = 0
    district_counts: Counter[str] = Counter()

    for college in colleges:
        district = match_district(college.name, alias_index)
        city = guess_city(college.name)
        if district:
            matched_district += 1
            district_counts[district] += 1
        if city:
            matched_city += 1
        if args.apply:
            college.district = district
            college.city = city

    if args.apply:
        db.commit()
        print("Applied changes to the database.")
    else:
        print("Dry run - no changes written. Re-run with --apply to save.")

    print(f"\ndistrict matched: {matched_district}/{len(colleges)} ({matched_district*100//len(colleges)}%)")
    print(f"city (best-effort) matched: {matched_city}/{len(colleges)} ({matched_city*100//len(colleges)}%)")
    print("\nDistrict distribution:")
    for d, c in district_counts.most_common():
        print(f"  {d}: {c}")

    db.close()


if __name__ == "__main__":
    main()
