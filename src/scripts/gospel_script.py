# ============================================================
# VIDEOFACTORY - GOSPEL SCRIPT ENGINE
# Reels-optimized scripts: Hook + Body + CTA
# Each line = one cut (2-3 seconds)
# Total: 20-30 seconds per reel
# ============================================================

import random
from datetime import datetime


# ============================================================
# SCRIPT STRUCTURE EXPLAINED
# ============================================================
# hook   = First 3 seconds - must grab attention immediately
# body   = Main message - short punchy lines
# cta    = Last 3 seconds - call to action
# tags   = YouTube/Instagram tags
# title  = Video title suggestion
# thumb  = Thumbnail text suggestion


GOSPEL_SCRIPTS = [

    {
        "id": "gospel_001",
        "title": "God Has Not Forgotten You",
        "thumb": "GOD HAS NOT\nFORGOTTEN YOU",
        "hook": "God has not forgotten you.",
        "body": [
            "Even in your darkest moment.",
            "Even when prayers feel unanswered.",
            "Even when you feel completely alone.",
            "He sees every tear you have cried.",
            "He knows every battle you are fighting.",
            "Isaiah forty one ten says,",
            "Fear not, for I am with you.",
            "Be not dismayed, for I am your God.",
            "He is still working on your behalf.",
            "Your breakthrough is coming.",
        ],
        "cta": "Share this with someone who needs it today.",
        "tags": ["gospel", "faith", "christian", "prayer", "god", "motivation", "bible", "worship"],
        "mood": "peaceful",
        "duration_estimate": 27,
    },

    {
        "id": "gospel_002",
        "title": "This Prayer Will Change Your Morning",
        "thumb": "PRAY THIS\nEVERY MORNING",
        "hook": "Pray this every single morning.",
        "body": [
            "Lord, I surrender this day to you.",
            "Order my steps.",
            "Guard my mind.",
            "Protect my family.",
            "Open doors no man can shut.",
            "Give me wisdom beyond my own.",
            "Let your favor go before me today.",
            "I trust you with everything.",
        ],
        "cta": "Say Amen if you receive this prayer.",
        "tags": ["morning prayer", "christian", "gospel", "faith", "prayer", "amen", "god"],
        "mood": "hopeful",
        "duration_estimate": 24,
    },

    {
        "id": "gospel_003",
        "title": "God is Still Working",
        "thumb": "GOD IS STILL\nWORKING",
        "hook": "It is not over.",
        "body": [
            "What looks like a delay is preparation.",
            "What looks like a closed door is redirection.",
            "What feels like silence is God working behind the scenes.",
            "Abraham waited twenty five years.",
            "Joseph waited thirteen years.",
            "Your wait has a purpose.",
            "Do not give up on what God promised you.",
            "He is faithful.",
            "He has never failed.",
        ],
        "cta": "Type YES if you still believe.",
        "tags": ["faith", "gospel", "christian", "trust god", "bible", "prayer", "hope"],
        "mood": "powerful",
        "duration_estimate": 26,
    },

    {
        "id": "gospel_004",
        "title": "Before You Sleep Tonight",
        "thumb": "BEFORE YOU\nSLEEP TONIGHT",
        "hook": "Before you sleep tonight, hear this.",
        "body": [
            "God loves you unconditionally.",
            "Your mistakes do not define you.",
            "His mercies are new every morning.",
            "Tomorrow is a fresh start.",
            "Cast all your worries on Him.",
            "He cares deeply for you.",
            "You are not alone in this.",
            "Rest now. He is watching over you.",
        ],
        "cta": "Share this with someone who needs rest tonight.",
        "tags": ["christian", "gospel", "faith", "goodnight", "prayer", "god", "peace"],
        "mood": "peaceful",
        "duration_estimate": 25,
    },

    {
        "id": "gospel_005",
        "title": "God Will Make a Way",
        "thumb": "GOD WILL\nMAKE A WAY",
        "hook": "God will make a way where there seems to be no way.",
        "body": [
            "Your situation is not too hard for Him.",
            "Your problem is not too big for Him.",
            "He parted the Red Sea.",
            "He brought water from a rock.",
            "He raised the dead.",
            "What makes you think He cannot help you?",
            "Speak this out loud right now.",
            "God is making a way for me.",
        ],
        "cta": "Say it with me. God is making a way.",
        "tags": ["gospel", "faith", "god", "christian", "miracle", "prayer", "bible", "breakthrough"],
        "mood": "powerful",
        "duration_estimate": 28,
    },

    {
        "id": "gospel_006",
        "title": "You Are Not Too Far Gone",
        "thumb": "YOU ARE NOT\nTOO FAR GONE",
        "hook": "You are not too far gone for God's grace.",
        "body": [
            "No matter what you have done.",
            "No matter how many times you have fallen.",
            "His grace is bigger than your worst mistake.",
            "The prodigal son came home broken.",
            "And the father ran to meet him.",
            "That is exactly how God sees you.",
            "Come back.",
            "He is waiting with open arms.",
        ],
        "cta": "Type GRACE if this spoke to you.",
        "tags": ["gospel", "grace", "christian", "faith", "god", "forgiveness", "bible"],
        "mood": "emotional",
        "duration_estimate": 26,
    },

    {
        "id": "gospel_007",
        "title": "Healing Prayer - Receive It Now",
        "thumb": "RECEIVE YOUR\nHEALING NOW",
        "hook": "Receive your healing right now in Jesus name.",
        "body": [
            "Place your hand where it hurts.",
            "Father, I declare healing over your child.",
            "Every sickness must bow at the name of Jesus.",
            "Every pain, every disease, every weakness.",
            "By His stripes we are healed.",
            "Isaiah fifty three five.",
            "Receive it now.",
            "Believe it. It is done.",
        ],
        "cta": "Type HEALED if you receive this prayer.",
        "tags": ["healing prayer", "gospel", "christian", "faith", "jesus", "miracle", "prayer"],
        "mood": "powerful",
        "duration_estimate": 25,
    },

]


# ============================================================
# SWAHILI GOSPEL SCRIPTS
# ============================================================

SWAHILI_SCRIPTS = [

    {
        "id": "sw_gospel_001",
        "title": "Mungu Hakukusahau",
        "thumb": "MUNGU\nHAKUKUSAHAU",
        "hook": "Mungu hakukusahau.",
        "body": [
            "Hata katika wakati wako mgumu zaidi.",
            "Hata maombi yanapoona hayajibiwa.",
            "Hata unapohisi peke yako kabisa.",
            "Anaona kila machozi unayolia.",
            "Anajua kila vita unayopigana.",
            "Usife tamaa.",
            "Yeye bado anafanya kazi kwa ajili yako.",
            "Ufumbuzi wako unakuja.",
        ],
        "cta": "Shiriki hii na mtu anayehitaji leo.",
        "tags": ["injili", "imani", "mungu", "sala", "kristo", "tumaini"],
        "mood": "peaceful",
        "duration_estimate": 24,
    },

    {
        "id": "sw_gospel_002",
        "title": "Sala ya Asubuhi",
        "thumb": "SALA YA\nASUBUHI",
        "hook": "Sema sala hii kila asubuhi.",
        "body": [
            "Baba, nakukabidhi siku hii.",
            "Ongoza hatua zangu.",
            "Linda akili yangu.",
            "Linda familia yangu.",
            "Fungua milango ambayo hakuna mtu awezaye kuifunga.",
            "Nipe hekima inayozidi yangu mwenyewe.",
            "Neema yako itangulie mbele yangu leo.",
            "Nakuamini wewe na kila kitu.",
        ],
        "cta": "Sema Amina ukipokea sala hii.",
        "tags": ["sala", "asubuhi", "injili", "imani", "mungu", "amina"],
        "mood": "hopeful",
        "duration_estimate": 25,
    },

]


# ============================================================
# MOTIVATIONAL SCRIPTS (for that niche too)
# ============================================================

MOTIVATIONAL_SCRIPTS = [

    {
        "id": "motiv_001",
        "title": "Stop Waiting for the Perfect Moment",
        "thumb": "STOP\nWAITING",
        "hook": "The perfect moment does not exist.",
        "body": [
            "Every successful person started before they were ready.",
            "They started scared.",
            "They started with nothing.",
            "But they started.",
            "You have been waiting too long.",
            "Your idea is good enough.",
            "You are good enough.",
            "Start today. Right now.",
        ],
        "cta": "Save this and start something today.",
        "tags": ["motivation", "success", "mindset", "start", "inspiration", "goals"],
        "mood": "powerful",
        "duration_estimate": 22,
    },

    {
        "id": "motiv_002",
        "title": "You Are One Decision Away",
        "thumb": "ONE DECISION\nAWAY",
        "hook": "You are one decision away from a different life.",
        "body": [
            "One decision to wake up earlier.",
            "One decision to stop making excuses.",
            "One decision to invest in yourself.",
            "One decision to walk away from what drains you.",
            "One decision to believe you are capable.",
            "That decision is available to you right now.",
            "Make it.",
        ],
        "cta": "Drop a fire emoji if you needed this today.",
        "tags": ["motivation", "mindset", "success", "decision", "life", "inspiration"],
        "mood": "powerful",
        "duration_estimate": 21,
    },

]


# ============================================================
# SCRIPT MANAGER CLASS
# ============================================================

class ScriptManager:

    def __init__(self, niche="gospel", language="english"):
        self.niche = niche
        self.language = language
        self._load_scripts()

    def _load_scripts(self):
        if self.niche == "swahili" or self.language == "swahili" or str(self.niche).startswith("swahili"):
            try:
                from src.scripts.swahili_script import SWAHILI_SCRIPT_DATABASE
                self.scripts = []
                for cat in SWAHILI_SCRIPT_DATABASE.values():
                    self.scripts.extend(cat)
            except Exception:
                self.scripts = SWAHILI_SCRIPTS
        elif self.niche == "gospel" and self.language == "english":
            self.scripts = GOSPEL_SCRIPTS
        elif self.niche == "motivational":
            self.scripts = MOTIVATIONAL_SCRIPTS
        else:
            self.scripts = GOSPEL_SCRIPTS

    def get_random_script(self):
        return random.choice(self.scripts)

    def get_script_by_id(self, script_id):
        for s in self.scripts:
            if s["id"] == script_id:
                return s
        return None

    def get_all_scripts(self):
        return self.scripts

    def get_full_text(self, script):
        lines = [script["hook"]] + script["body"] + [script["cta"]]
        return " ".join(lines)

    def get_lines(self, script):
        return [script["hook"]] + script["body"] + [script["cta"]]


    def get_script_by_index(self, index=0):
        if not self.scripts:
            return None
        index = max(0, min(index, len(self.scripts) - 1))
        return self.scripts[index]

    def list_scripts(self):
        print("")
        print("=" * 55)
        print(f"  Available Scripts - {self.niche.upper()} / {self.language.upper()}")
        print("=" * 55)
        for i, s in enumerate(self.scripts, 1):
            print(f"  {i:02d}. [{s['id']}] {s['title']}")
            print(f"       Hook: {s['hook']}")
            print(f"       Lines: {len(s['body'])} | Est: {s['duration_estimate']}s")
            print("")
        print("=" * 55)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n--- GOSPEL ENGLISH ---")
    mgr = ScriptManager(niche="gospel", language="english")
    mgr.list_scripts()

    script = mgr.get_random_script()
    print(f"\nRandom Pick: {script['title']}")
    print(f"Hook: {script['hook']}")
    print(f"Lines: {len(mgr.get_lines(script))}")
    print(f"Full text preview:")
    print(mgr.get_full_text(script)[:200] + "...")

    print("\n--- SWAHILI ---")
    mgr_sw = ScriptManager(niche="gospel", language="swahili")
    mgr_sw.list_scripts()
