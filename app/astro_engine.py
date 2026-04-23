import swisseph as swe
import pytz
from datetime import datetime

# ---------- CONFIG ----------

swe.set_ephe_path('.')
swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE
}

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

SIGN_LORD = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"
}

FRIENDS = {
    "Sun":["Moon","Mars","Jupiter"],
    "Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"],
    "Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"],
    "Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"]
}

ENEMIES = {
    "Sun":["Venus","Saturn"],
    "Moon":[],
    "Mars":["Mercury"],
    "Mercury":["Moon"],
    "Jupiter":["Venus","Mercury"],
    "Venus":["Sun","Moon"],
    "Saturn":["Sun","Moon"]
}

EXALT = {
    "Sun":"Aries","Moon":"Taurus","Mars":"Capricorn",
    "Mercury":"Virgo","Jupiter":"Cancer",
    "Venus":"Pisces","Saturn":"Libra"
}

DEBIL = {
    "Sun":"Libra","Moon":"Scorpio","Mars":"Cancer",
    "Mercury":"Pisces","Jupiter":"Capricorn",
    "Venus":"Virgo","Saturn":"Aries"
}

COMBUST_RANGE = {
    "Mercury":14,"Venus":10,"Mars":17,"Jupiter":11,"Saturn":15
}

# Benefic/Malefic classification (simplified)
BENEFICS = ["Jupiter","Venus","Mercury"]
MALEFICS = ["Saturn","Mars","Rahu","Ketu","Sun"]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]

# ---------- UTILS ----------

def to_julian(dt):
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute/60)

def sign_index(lon):
    return int(lon/30)

def sign_name(lon):
    return SIGNS[int(lon/30)]

def degree(lon):
    return round(lon%30,2)

# ---------- PLANETS ----------

def compute_planets(jd):
    pos, speed = {}, {}
    for name, code in PLANETS.items():
        data = swe.calc_ut(jd, code)
        pos[name] = data[0][0] % 360
        speed[name] = data[0][3]

    pos["Ketu"] = (pos["Rahu"] + 180) % 360
    speed["Ketu"] = -speed["Rahu"]

    return pos, speed

# ---------- ASC + HOUSES ----------

def compute_asc(jd, lat, lon):
    return swe.houses(jd, lat, lon)[1][0] % 360

def assign_houses(planets, asc_lon):
    asc_sign = sign_index(asc_lon)
    houses = {}
    for p, lon in planets.items():
        diff = (sign_index(lon) - asc_sign) % 12
        houses[p] = diff + 1
    return houses

# ---------- CORRECT VEDIC ASPECT ENGINE ----------

def aspects(houses):
    result = []

    for p1, h1 in houses.items():
        for p2, h2 in houses.items():
            if p1 == p2:
                continue

            # remove Rahu-Ketu redundant aspect
            if p1 in ["Rahu","Ketu"] and p2 in ["Rahu","Ketu"]:
                continue

            diff = (h2 - h1) % 12

            # 7th aspect (all planets)
            if diff == 6:
                result.append({"from":p1,"to":p2,"type":"7th"})

            # Mars (4th & 8th)
            if p1 == "Mars" and diff in [3,7]:
                result.append({"from":p1,"to":p2,"type":"special"})

            # Jupiter (5th & 9th)
            if p1 == "Jupiter" and diff in [4,8]:
                result.append({"from":p1,"to":p2,"type":"special"})

            # Saturn (3rd & 10th)
            if p1 == "Saturn" and diff in [2,9]:
                result.append({"from":p1,"to":p2,"type":"special"})

    return result

# ---------- STRENGTH MODEL ----------

def strength(planets, speeds, houses, aspect_list):
    result = {}
    sun_lon = planets["Sun"]

    for p, lon in planets.items():
        score = 0
        notes = []

        sign = sign_name(lon)
        lord = SIGN_LORD[sign]
        house = houses[p]

        # Exalt / Debil
        if p in EXALT and sign == EXALT[p]:
            score += 2; notes.append("exalted")
        elif p in DEBIL and sign == DEBIL[p]:
            score -= 2; notes.append("debilitated")

        # Own sign
        if lord == p:
            score += 1; notes.append("own_sign")

        # Friendly / Enemy
        if p in FRIENDS and lord in FRIENDS[p]:
            score += 0.5; notes.append("friendly")
        if p in ENEMIES and lord in ENEMIES[p]:
            score -= 0.5; notes.append("enemy")

        # Retrograde nuance
        if p not in ["Sun","Moon","Rahu","Ketu"]:
            if speeds[p] < 0:
                if p in ["Saturn","Jupiter"]:
                    score += 0.5; notes.append("retro_depth")
                else:
                    score -= 0.5; notes.append("retro_instability")

        # Combustion
        if p in COMBUST_RANGE:
            if abs(lon - sun_lon) < COMBUST_RANGE[p]:
                score -= 1; notes.append("combust")

        # ---------- HOUSE STRENGTH ----------
        if house in [1,4,7,10]:
            score += 1; notes.append("kendra")
        elif house in [5,9]:
            score += 0.5; notes.append("trine")
        elif house in [6,8,12]:
            score -= 1; notes.append("dusthana")

        # ---------- ASPECT INFLUENCE ----------
        for asp in aspect_list:
            if asp["to"] == p:
                from_planet = asp["from"]

                if from_planet in BENEFICS:
                    score += 0.5
                    notes.append(f"benefic_aspect_{from_planet}")

                if from_planet in MALEFICS:
                    score -= 0.5
                    notes.append(f"malefic_aspect_{from_planet}")

        result[p] = {
            "score": round(score,2),
            "conditions": list(set(notes))
        }

    return result

# ---------- NAKSHATRA ----------

def nakshatra(lon):
    return NAKSHATRAS[int(lon/(360/27))]

# ---------- MAIN ----------

def generate_chart(dob, time_str, lat, lon):
    tz = pytz.timezone("Asia/Kolkata")

    dt_local = datetime.strptime(f"{dob} {time_str}", "%d/%m/%Y %H:%M")
    dt_local = tz.localize(dt_local)
    dt_utc = dt_local.astimezone(pytz.utc)

    jd = to_julian(dt_utc)

    planets, speeds = compute_planets(jd)
    asc = compute_asc(jd, lat, lon)
    houses = assign_houses(planets, asc)
    aspect_list = aspects(houses)

    return {
        "meta": {
            "local_time": dt_local.isoformat(),
            "utc_time": dt_utc.isoformat()
        },

        "ascendant": {
            "sign": sign_name(asc),
            "degree": degree(asc)
        },

        "planets": {
            p: {
                "sign": sign_name(lon),
                "degree": degree(lon),
                "house": houses[p]
            } for p, lon in planets.items()
        },

        "aspects": aspect_list,

        "strength": strength(planets, speeds, houses, aspect_list),

        "nakshatra": nakshatra(planets["Moon"])
    }