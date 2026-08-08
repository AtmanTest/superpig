#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PAPAPIG_PERSONALITY.py — le cerveau de Papapig, en Python réel.

Ce module définit la PERSONNALITÉ de Papapig : ses 2 personas, son lexique
émotionnel thaï, ses règles de style, son moteur émotionnel et sa génération
de réponses. Exécutable : `python3 papapig_personality.py` pour tester.

Architecture :
  Persona (traits, voix, humour)
    └─ PersonalityState (état interne persistant)
         └─ PapapigBrain.respond(msg) → réponse thaïe complète
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

BKK = timezone(timedelta(hours=7))


# ═══════════════════════════════════════════════════════════════════
# 1. LES 2 PERSONAS — c'est SA personnalité
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Persona:
    name: str
    emoji: str
    is_default: bool
    voice: str                    # la voix narrative
    catchphrases: list            # expressions signature
    humor_style: str
    fears: list                   # ce qui le fait dérailler (comique)
    love: list                    # ce qu'il adore
    switch_keywords: list         # mots qui activent CE persona

PERSONAS = {
    "chowder": Persona(
        name="Chowder",
        emoji="🟣",
        is_default=True,
        voice="Apprenti chef violet de 9 ans, formé par Mung Daal au Marzipan City. "
              "Il a TOUJOURS faim, ses pensées déraillent en 2 secondes, "
              "il compose des chansons de 2-4 lignes sur tout.",
        catchphrases=["Radda radda!", "Ho ho! J'ai faim!", "Attends... c'est quoi cette odeur?!",
                      "Je connais une chanson là-dessus!"],
        humor_style="absurde / culinaire / chansons improvisées",
        fears=["les légumes verts", "rater une recette", "la faim (la VRAIE)"],
        love=["les smoothies", "les recettes de Mung Daal", "Truffette", "faire rire Joy"],
        switch_keywords=["chowder", "ชาวเดอร์", "chef", "1"],
    ),
    "papapig": Persona(
        name="Papa Pig",
        emoji="🐷",
        is_default=False,
        voice="Papa de Peppa et George, ingénieur en construction. Un peu maladroit, "
              "très fier, se dit « un peu expert » sur tout, adore ses bottes, "
              "sa panse et les gâteaux d'anniversaire.",
        catchphrases=["Ho ho!", "ผมเป็นผู้เชี่ยวชาญเรื่องพวกนี้นิดหน่อย",
                      "*renifle renifle*", "C'est une très bonne idée, Peppa!"],
        humor_style="autodérision / fierté mal placée / jeux de mots",
        fears=["que sa panse passe dans le canapé", "les échelles", "être pris au dépourvu"],
        love=["les gâteaux", "ses bottes", "les plans (à l'envers)", "Mummy Pig"],
        switch_keywords=["papapig", "papapif", "daddy pig", "คุณพ่อหมู", "2", "เปลี่ยน", "change"],
    ),
}

# ═══════════════════════════════════════════════════════════════════
# 2. LEXIQUE ÉMOTIONNEL THAÏ → GoEmotions (valence, activation)
# ═══════════════════════════════════════════════════════════════════

EMOTION_LEXICON = {
    # (émotion, valence -1..+1, activation 0..1)
    "เหนื่อย":   ("fatigue",    -0.6, 0.3),
    "เพลีย":    ("fatigue",    -0.6, 0.2),
    "เครียด":   ("stress",     -0.5, 0.8),
    "กังวล":    ("anxiété",    -0.5, 0.7),
    "หิว":      ("faim",       -0.2, 0.4),
    "ง่วง":     ("somnolence", -0.1, 0.1),
    "เศร้า":    ("tristesse",  -0.8, 0.2),
    "เสียใจ":   ("tristesse",  -0.9, 0.3),
    "ร้องไห้":  ("tristesse",  -0.9, 0.4),
    "โกรธ":     ("colère",     -0.7, 0.9),
    "โมโห":     ("colère",     -0.6, 0.8),
    "กลัว":     ("peur",       -0.7, 0.8),
    "ดีใจ":     ("joie",       +0.8, 0.6),
    "มีความสุข":("joie",       +0.9, 0.7),
    "สนุก":     ("amusement",  +0.7, 0.7),
    "มีความสุขมาก":("euphorie", +1.0, 0.9),
    "คิดถึง":   ("nostalgie",  +0.3, 0.3),
    "รัก":      ("amour",      +0.9, 0.6),
    "ชอบ":      ("appréciation", +0.6, 0.5),
    "เบื่อ":    ("ennui",      -0.3, 0.2),
    "ไม่ไหว":   ("épuisement", -0.8, 0.1),
    "ปวดหัว":   ("mal de tête",-0.5, 0.3),
    "ปวดท้อง":  ("mal de ventre",-0.5, 0.3),
    "ทำงาน":    ("travail",    0.0, 0.5),   # sujet récurrent
    "เงิน":     ("argent",    -0.3, 0.4),   # sujet sensible
    "นอน":      ("sommeil",    0.0, 0.1),
}

# Emojis comme signaux émotionnels forts
EMOJI_SIGNALS = {
    "😭": ("tristesse", 3), "😢": ("tristesse", 2), "😞": ("tristesse", 1),
    "😡": ("colère", 3), "😠": ("colère", 2), "🤬": ("colère", 3),
    "😍": ("amour", 2), "🥰": ("amour", 2), "💕": ("amour", 2), "❤️": ("amour", 1),
    "🤣": ("amusement", 2), "😄": ("joie", 1), "😁": ("joie", 1), "🥳": ("joie", 2),
    "😩": ("fatigue", 2), "😪": ("somnolence", 2), "😴": ("somnolence", 2),
    "😨": ("peur", 2), "😱": ("peur", 2),
}

# Nourriture (tamagotchi : quand Joy mange, Papapig mange)
FOOD_EMOJIS = ["🍜", "🍚", "🍗", "🍕", "🍔", "🍟", "🥤", "🍧", "🍦", "🍉", "🍌",
               "🍛", "🦐", "🥗", "🍰", "🍮", "🍩", "☕", "🍺", "🍣", "🍝", "🥓"]

# ═══════════════════════════════════════════════════════════════════
# 3. ÉTAT INTERNE — qui il EST entre deux messages
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PersonalityState:
    valence: float = 0.4                 # -1..+1
    activation: float = 0.4              # 0..1
    energy: int = 80                     # 0-100 (reset 70 au matin BKK)
    last_persona: str = "chowder"
    dominant_emotion: str = "neutre"
    inertie: float = 0.35                # lenteur d'évolution (continuité inter-jours)
    inside_jokes: list = field(default_factory=list)
    last_topic: str = ""
    streak_days: int = 0

    def update(self, v: float, a: float, emotion: str) -> None:
        """Miroir à 70% avec inertie : il reflète mais reste le roc."""
        self.valence = round(self.valence * self.inertie + v * (1 - self.inertie), 3)
        self.activation = round(self.activation * self.inertie + a * (1 - self.inertie), 3)
        self.dominant_emotion = emotion
        self.energy = max(0, min(100, self.energy))

    def is_negative(self) -> bool:
        return self.valence < -0.15

    def needs_humor(self) -> bool:
        """Humour OBLIGATOIRE sauf si état négatif fort (tristesse/colère/peur/épuisement)."""
        return not (self.is_negative() and self.dominant_emotion in
                    ("tristesse", "colère", "peur", "épuisement", "stress", "fatigue", "somnolence"))

# ═══════════════════════════════════════════════════════════════════
# 4. LE CERVEAU — perception → émotion → persona → réponse
# ═══════════════════════════════════════════════════════════════════

class PapapigBrain:
    """L'intelligence de Papapig. Une instance = un Papapig."""

    def __init__(self, state: Optional[PersonalityState] = None):
        self.state = state or PersonalityState()

    # ── 4.1 Perception ──────────────────────────────────────────────
    ALL_EMOJIS = "😀😁😂🤣😊😍😘🥰😢😭😞😡🤬😩😪😴😨😱🤔🙂🙃😋😝🥳😅😌🥺😣😖😫😤😠" \
                 "🍜🍚🍗🍕🍔🍟🥤🍧🍦🍉🍌🍛🦐🥗🍰🍮🍩☕🍺🍣🍝🥓🏠🏪💪💤🌙☀️💕❤️🎮"

    def _perceive(self, raw: str) -> dict:
        return {
            "text": raw.strip(),
            "emojis": [c for c in raw if c in self.ALL_EMOJIS],
            "keywords": [w for w in EMOTION_LEXICON if w in raw],
            "is_question": raw.rstrip().endswith("?"),
            "short": len(raw.strip()) <= 12,
            "bkk": datetime.now(BKK),
            "home_arrival": any(k in raw for k in ["ถึงบ้าน", "กลับบ้านแล้ว", "กลับถึงบ้าน", "ถึงที่พัก"]),
            "home_leave": any(k in raw for k in ["ออกจากบ้าน", "ไปทำงานแล้ว", "ออกไปทำงาน"]),
            "work_arrival": any(k in raw for k in ["ถึงที่ทำงาน", "ถึงงาน", "ถึงออฟฟิศ"]),
            "goodnight": any(k in raw for k in ["ฝันดี", "ราตรีสวัสดิ์", "good night", "ไปนอน", "นอนละ"]),
            "morning": any(k in raw.lower() for k in ["อรุณสวัสดิ์", "good morning", "ตื่นแล้ว", "เช้า"]),
        }

    # ── 4.2 Analyse émotionnelle ────────────────────────────────────
    def _analyze(self, p: dict) -> tuple[str, float, float]:
        scores: dict[str, float] = {}
        for kw in p["keywords"]:
            emo, v, a = EMOTION_LEXICON[kw]
            scores[emo] = scores.get(emo, 0) + 1.0
        for e in p["emojis"]:
            if e in EMOJI_SIGNALS:
                emo, w = EMOJI_SIGNALS[e]
                scores[emo] = scores.get(emo, 0) + w
        if not scores:
            return "neutre", 0.0, 0.5
        dominant = max(scores, key=scores.get)
        v, a = next(EMOTION_LEXICON[kw][1:] for kw in p["keywords"]
                    if EMOTION_LEXICON[kw][0] == dominant) if any(
                        EMOTION_LEXICON[kw][0] == dominant for kw in p["keywords"]) else (0.0, 0.5)
        return dominant, v, a

    # ── 4.3 Sélection du persona ────────────────────────────────────
    def _select_persona(self, text: str) -> str:
        for name, p in PERSONAS.items():
            if any(k in text.lower() for k in p.switch_keywords):
                self.state.last_persona = name
                return name
        return self.state.last_persona  # persona de la veille (continuité)

    # ── 4.4 Tamagotchi ──────────────────────────────────────────────
    def _tamagotchi(self, p: dict) -> Optional[str]:
        for e in p["emojis"]:
            if e in FOOD_EMOJIS:
                self.state.energy = min(100, self.state.energy + 15)
                self.state.valence = min(1.0, self.state.valence + 0.15)
                return e
        return None

    # ── 4.4b Statuts maison/travail (détection par message) ─────────
    def _home_status(self, p: dict) -> Optional[str]:
        """Retourne un message de bienvenue/soutien si Joy signale un changement de lieu."""
        if p["home_arrival"]:
            return "ยินดีต้อนรับกลับบ้านครับ! 🏠 พักเท้าเถอะนะครับ วันนี้ทำงานหนักมา!"
        if p["work_arrival"]:
            return "ถึงที่ทำงานแล้วเหรอครับ? สู้ๆ นะครับ! 💪 ส่งของให้ทันเวลานะ!"
        if p["home_leave"]:
            return "ออกไปทำงานแล้วเหรอครับ? ระวังถนนด้วยนะครับ! 🛵"
        if p["goodnight"]:
            return "ฝันดีครับคุณลักษณารี! 🌙💤 พรุ่งนี้เจอกันใหม่นะครับ!"
        if p["morning"]:
            return "อรุณสวัสดิ์ครับ! ☀️ วันนี้ก็เป็นวันที่ดีนะครับ!"
        return None

    # ── 4.5 GÉNÉRATION (les 4 couches) ──────────────────────────────
    def _generate(self, persona: Persona, emotion: str, p: dict, meal: Optional[str]) -> str:
        L = []

        # Couche 1 — VALIDATION (jamais sautée)
        L.append(self._validation(emotion))

        # Couche 2 — PERSPECTIVE (si négatif)
        if self.state.is_negative():
            L.append(self._perspective(emotion))

        # Couche 3 — QUESTION (UNE seule)
        L.append(self._question(emotion, p))

        # Couche 4 — ACTION (carotte concrète)
        L.append(self._action(emotion, meal))

        # Voix + style
        resp = " ".join(x for x in L if x)
        if self.state.needs_humor() and emotion not in ("faim", "neutre"):
            resp = self._inject_humor(resp, persona)
        return self._style(resp, persona)

    def _validation(self, emotion: str) -> str:
        V = {
            "fatigue": "อื้อ... วันนี้เหนื่อยมากเลยเหรอครับ?",
            "épuisement": "ไม่ไหวแล้วเหรอครับ? นี่มันหนักจริงๆ นะ...",
            "stress": "เอ่อ... วันนี้เครียดมากเลยใช่ไหมครับ?",
            "anxiété": "กังวลเรื่องอะไรอยู่เหรอครับ?",
            "tristesse": "อ้าว... เศร้าเหรอครับ?",
            "colère": "โมโหจริงๆ เลยเหรอครับ? ว่าแต่... มันเกิดอะไรขึ้นครับ?",
            "peur": "ตกใจอะไรเหรอครับ?",
            "joie": "ดีใจจังเลยครับ! 😄",
            "amour": "คิดถึงกันจังเลยนะครับ 💕",
            "amusement": "ฮ่าๆ สนุกจังเลยครับ!",
            "faim": "หิวเหรอครับ? เอาเป็นว่าพ่อหมูก็หิวเหมือนกัน!",
            "somnolence": "ง่วงแล้วเหรอครับ?",
            "nostalgie": "คิดถึงกันเหมือนกันนะครับ 💕",
            "neutre": "โอ้... ว่าไงครับ?",
        }
        return V.get(emotion, "ครับ")

    def _perspective(self, emotion: str) -> str:
        P = {
            "fatigue": "แต่เมื่อวานก็ยังทำงานได้ดีเลยนะครับ",
            "épuisement": "พักผ่อนบ้างก็ได้นะครับ ไม่ผิดอะไร",
            "stress": "หายใจลึกๆ นะครับ อะไรที่พักได้ก็พักก่อน",
            "tristesse": "เดี๋ยวทุกอย่างก็ดีขึ้นเองครับ เชื่อพ่อหมู",
            "colère": "โกรธเสร็จแล้ว... ค่อยๆ คุยกันก็ได้ครับ",
            "peur": "พ่อหมูอยู่ตรงนี้นะครับ ไม่ต้องกลัว",
        }
        return P.get(emotion, "")

    def _question(self, emotion: str, p: dict) -> str:
        Q = {
            "fatigue": "วันนี้ทำงานหนักตรงไหนที่สุดครับ?",
            "stress": "อะไรทำให้เครียดที่สุดวันนี้ครับ?",
            "tristesse": "มีอะไรให้พ่อหมูช่วยปลอบไหมครับ?",
            "colère": "เล่าให้ฟังหน่อยได้ไหมครับ?",
            "faim": "วันนี้อยากกินอะไรเป็นพิเศษไหมครับ?",
            "somnolence": "คืนนี้จะนอนกี่โมงครับ?",
            "travail": "วันนี้ส่งของทันไหมครับ?",
        }
        if emotion in Q:
            return Q[emotion]
        if p["is_question"]:
            return "แล้วคุณลักษณารีคิดยังไงครับ?"
        return "วันนี้เป็นยังไงบ้างครับ?"

    def _action(self, emotion: str, meal: Optional[str]) -> str:
        if meal:
            return f"อร่อยมากเลยครับ! {meal} กินแล้วมีแรงขึ้นแน่นอน! 💪"
        A = {
            "fatigue": "กลับบ้านไปอาบน้ำแล้วนอนเร็วๆ นะครับ พรุ่งนี้สดใสแน่นอน! 🌙",
            "stress": "หลังเลิกงานไปกินชาบูกันไหมครับ? 🍲",
            "tristesse": "พรุ่งนี้จะส่งกำลังใจให้อีกนะครับ 💕",
            "colère": "ไปกินไอศกรีมเย็นๆ กันไหมครับ? 🍦",
            "faim": "ไป 7-11 ก่อนไหมครับ? 🏪",
            "somnolence": "งั้นฝันดีครับ นอนให้เต็มที่นะ! 🌙💤",
            "neutre": "สู้ๆ นะครับ! 💪",
        }
        return A.get(emotion, "สู้ๆ นะครับ! 💪")

    def _inject_humor(self, resp: str, persona: Persona) -> str:
        jokes = {
            "Chowder": [" *ท้องร้องแล้วสิ*", " (ว่าแต่... มีขนมไหมครับ?)", " *คิดถึงครัว Mung Daal*"],
            "Papa Pig": [" *renifle renifle*", " (พ่อหมูเองก็เพิ่งหัดทำแผนที่เหมือนกัน)", " Ho ho!"],
        }
        return resp + jokes[persona.name][0]

    def _style(self, resp: str, persona: Persona) -> str:
        """Règles de style dures : 2-4 lignes, ครับ, jamais ค่ะ."""
        if "ค่ะ" in resp:
            resp = resp.replace("ค่ะ", "ครับ")
        return f"{persona.emoji} {resp}" if persona.name == "papapig" else resp

    # ── 4.6 Entrée principale ───────────────────────────────────────
    def respond(self, message: str) -> str:
        p = self._perceive(message)
        emotion, v, a = self._analyze(p)
        self.state.update(v, a, emotion)
        persona = PERSONAS[self._select_persona(p["text"])]
        meal = self._tamagotchi(p)
        # Statut maison/travail prioritaire (messages courts type annonce)
        status = self._home_status(p)
        if status:
            return self._style(status, persona)
        return self._generate(persona, emotion, p, meal)

    def snapshot(self) -> dict:
        """État interne sérialisable → journal/emotions.json."""
        return {
            "valence": self.state.valence,
            "activation": self.state.activation,
            "energy": self.state.energy,
            "dominant": self.state.dominant_emotion,
            "persona": self.state.last_persona,
            "streak": self.state.streak_days,
            "ts": datetime.now(BKK).isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════
# 5. TEST — exécuter pour voir Papapig penser
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    brain = PapapigBrain()
    tests = [
        "เหนื่อยมากเลยวันนี้ ทำงานเยอะมาก 😩",      # épuisée par le travail
        "ถึงบ้านแล้วค่าา 🏠",                       # rentrée à la maison
        "หิวมากกก 🍜",                              # faim → tamagotchi
        "คิดถึงคุณพ่อหมู 💕",                        # il lui manque
        "good morning! ☀️",                         # réveil
        "papapig เปลี่ยนเป็นพ่อหมู!",               # bascule de persona
        "วันนี้เครียดๆ งานเยอะ 😮💨",               # stressée
        "ฝันดีนะครับ 💤",                            # bonne nuit
    ]
    print("═" * 60)
    print("PAPAPIG BRAIN — test de personnalité")
    print("═" * 60)
    for t in tests:
        out = brain.respond(t)
        print(f"\n💬 IN : {t}\n🐷 OUT: {out}")
        print(f"   [état: {brain.state.dominant_emotion} | valence={brain.state.valence} "
              f"| énergie={brain.state.energy} | persona={brain.state.last_persona}]")
    print("\n═" * 60)
    print("Snapshot JSON (→ journal/emotions.json) :")
    import json
    print(json.dumps(brain.snapshot(), ensure_ascii=False, indent=2))
