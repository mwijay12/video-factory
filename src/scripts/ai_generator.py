# -*- coding: utf-8 -*-
import os
import random
import asyncio
import httpx
import json
import re
from pathlib import Path
from datetime import datetime, time as dtime
from src.utils.retry import retry_async

def load_env():
    p = Path('.env')
    if not p.exists():
        return {}
    d = {}
    for line in p.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            d[k.strip()] = v.strip()
    return d

ENV = load_env()
GROQ_API_KEY = ENV.get('GROQ_API_KEY', '')
GEMINI_API_KEY = ENV.get('GEMINI_API_KEY', '')
GEMINI_KEYS = [k.strip() for k in ENV.get('GEMINI_KEYS', '').split(',') if k.strip()]
OPENROUTER_API_KEY = ENV.get('OPENROUTER_API_KEY', '') or (ENV.get('OPENROUTER_KEYS', '').split(',')[0].strip() if ENV.get('OPENROUTER_KEYS', '') else '')
OPENAI_API_KEY = ENV.get('OPENAI_API_KEY', '')
CLOUDFLARE_ACCOUNT_ID = ENV.get('CLOUDFLARE_ACCOUNT_ID', '')
CLOUDFLARE_API_TOKEN = ENV.get('CLOUDFLARE_API_TOKEN', '')

def _load_backup_accounts():
    """Load optional Cloudflare fallback accounts from env (never hardcode keys).

    Format: JSON array of {"account_id": "...", "api_token": "..."}
    """
    raw = ENV.get('CLOUDFLARE_BACKUP_ACCOUNTS', '').strip()
    if not raw:
        return []
    try:
        accounts = json.loads(raw)
    except Exception:
        print('  WARNING: CLOUDFLARE_BACKUP_ACCOUNTS is not valid JSON; ignoring.')
        return []
    clean = []
    for acct in accounts:
        if isinstance(acct, dict) and acct.get('account_id') and acct.get('api_token'):
            clean.append({
                'account_id': str(acct['account_id']),
                'api_token': str(acct['api_token']),
            })
    return clean


CLOUDFLARE_BACKUP_ACCOUNTS = _load_backup_accounts()

HISTORY_FILE = Path('output/.topic_history.json')

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        except:
            return []
    return []

async def generate_broll_search_queries_with_gemini(script_text: str) -> list:
    """Generates 2-3 visual B-roll search queries per line using Gemini AI."""
    prompt = (
        "You are an AI Video Director. Analyze the following script text and extract 2-3 specific, high-quality "
        "visual stock video search keywords (in English) for each major visual beat.\n"
        "Return ONLY a JSON array of strings (e.g. [\"nature sunset river\", \"gospel choir singing\", \"peaceful ocean waves\"]).\n\n"
        f"Script Text:\n{script_text}"
    )
    try:
        raw = await generate_with_gemini(prompt)
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  Gemini B-Roll Query error: {e}")
    return ["nature scenery", "gospel worship", "peaceful atmosphere"]

def save_history(h):
    HISTORY_FILE.parent.mkdir(exist_ok=True, parents=True)
    HISTORY_FILE.write_text(json.dumps(h, indent=2, ensure_ascii=False), encoding='utf-8')

def get_time_context():
    now = datetime.now().time()
    if dtime(5,0) <= now < dtime(11,0): return 'morning'
    if dtime(11,0) <= now < dtime(15,0): return 'afternoon'
    if dtime(15,0) <= now < dtime(20,0): return 'evening'
    return 'bedtime'

TIME_NICHE_MAP = {
    'morning':   ['gospel', 'prayer', 'motivational'],
    'afternoon': ['motivational', 'praise', 'gospel'],
    'evening':   ['gospel', 'praise', 'prayer'],
    'bedtime':   ['prayer', 'bedtime_prayer', 'gospel'],
}

TOPIC_POOLS = {
    'gospel': [
        'The shocking truth about what happened when Peter denied Jesus three times',
        'Why God allowed Joseph to suffer 13 years before becoming a ruler',
        'The hidden meaning behind why Jesus wept at Lazarus tomb',
        'What David did in the cave that changed his destiny forever',
        'The one prayer Jesus said in the garden that nobody talks about',
        'Why Job lost everything but gained something greater',
        'The real reason God chose Mary out of every woman',
        'What the woman at the well taught us about acceptance',
        'How the prodigal son story is actually about YOU right now',
        'The dangerous mistake the rich young ruler made',
        'Why Jesus chose fishermen instead of priests',
        'What Paul learned from his thorn in the flesh',
        'The miracle hidden in the feeding of 5000',
        'Why Daniel survived the lions when others did not',
        'The truth about Esther that nobody preaches',
        'What happens when God says NO to your prayer',
        'The lie the enemy keeps telling Christians today',
        'Why your suffering has a divine purpose',
        'The dangerous prayer that changed everything for Jabez',
        'What Moses learned in 40 years of waiting',
    ],
    'prayer': [
        'Pray this if you feel God has abandoned you tonight',
        'A dangerous prayer for breakthrough that the enemy hates',
        'Pray this before any decision you regret making',
        'The 60 second prayer that broke my anxiety',
        'Pray this when you cannot sleep at 3am',
        'A warfare prayer for your children today',
        'The prayer that healed my broken relationship',
        'Pray this when nothing seems to work',
        'A prayer for the one who is about to give up',
        'Pray this over your finances right now',
    ],
    'bedtime_prayer': [
        'A whispered prayer for peace before you sleep tonight',
        'Cast every worry on Him before you close your eyes',
        'A surrender prayer for restless souls tonight',
        'Whisper this prayer when fear keeps you awake',
        'A goodnight prayer for someone going through hell',
    ],
    'praise': [
        'Why praise is the weapon the enemy fears most',
        'What happens in the spirit when you worship in pain',
        'The breakthrough that comes from praising before the answer',
        'How Paul and Silas praise broke prison chains',
        'Why God inhabits the praise of His people',
    ],
    'motivational': [
        'The brutal truth about why you keep failing',
        'What successful people do at 5am that you wont',
        'Why your comfort zone is killing your destiny',
        'The lie that is keeping you average',
        'Stop blaming your past start owning your future',
        'Why most people die at 25 but are buried at 75',
        'The harsh reality about who you call friends',
    ],
    'swahili': [
        'Sababu Mungu aliruhusu Yusufu apate mateso miaka 13',
        'Ukweli wa siri kuhusu kile kilichotokea Petro alipomkana Yesu',
        'Sala hatari iliyomfanya Yabesi abarikiwe',
        'Kile Daudi alichofanya pangoni kilibadilisha hatima yake',
        'Kwa nini Mungu anasema HAPANA kwenye maombi yako',
        'Sala ya kuomba kabla ya kulala unaposhindwa kupata usingizi',
    ],
}

def pick_unique_topic(niche='gospel'):
    from src.utils.database import record_topic, get_used_topics
    pool = TOPIC_POOLS.get(niche, TOPIC_POOLS.get('gospel', []))
    used = set(get_used_topics(niche))
    
    available = [t for t in pool if t.strip().lower() not in used]
    if not available:
        available = pool
        
    chosen = random.choice(available)
    record_topic(chosen, niche)
    return chosen

MOOD_VARIANTS = {
    'gospel': [
        {'mood': 'emotional', 'voice': 'en-US-AriaNeural',        'rate': '-15%', 'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'peaceful',  'voice': 'en-US-AriaNeural',        'rate': '-18%', 'pitch': '-2Hz', 'style': 'normal'},
        {'mood': 'peaceful',  'voice': 'en-US-ChristopherNeural', 'rate': '-16%', 'pitch': '-2Hz', 'style': 'normal'},
        {'mood': 'hopeful',   'voice': 'en-US-GuyNeural',         'rate': '-12%', 'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'emotional', 'voice': 'en-US-JennyNeural',       'rate': '-14%', 'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'powerful',  'voice': 'en-US-GuyNeural',         'rate': '-8%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'cinematic', 'voice': 'en-US-DavisNeural',       'rate': '-10%', 'pitch': '-2Hz', 'style': 'normal'},
    ],
    'prayer': [
        {'mood': 'peaceful',  'voice': 'en-US-AriaNeural',        'rate': '-18%', 'pitch': '-2Hz', 'style': 'normal'},
        {'mood': 'emotional', 'voice': 'en-US-ChristopherNeural', 'rate': '-20%', 'pitch': '-3Hz', 'style': 'normal'},
        {'mood': 'holy',      'voice': 'en-GB-RyanNeural',        'rate': '-16%', 'pitch': '-2Hz', 'style': 'normal'},
    ],
    'bedtime_prayer': [
        {'mood': 'whisper',   'voice': 'en-US-AriaNeural',        'rate': '-24%', 'pitch': '-4Hz', 'style': 'whisper'},
        {'mood': 'whisper',   'voice': 'en-US-JennyNeural',       'rate': '-22%', 'pitch': '-3Hz', 'style': 'whisper'},
    ],
    'praise': [
        {'mood': 'powerful',  'voice': 'en-US-GuyNeural',         'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'hopeful',   'voice': 'en-US-JennyNeural',       'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'cinematic', 'voice': 'en-US-DavisNeural',       'rate': '-8%',  'pitch': '+0Hz', 'style': 'normal'},
    ],
    'motivational': [
        {'mood': 'powerful',  'voice': 'en-US-GuyNeural',         'rate': '-8%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'cinematic', 'voice': 'en-US-DavisNeural',       'rate': '-10%', 'pitch': '-2Hz', 'style': 'normal'},
        {'mood': 'emotional', 'voice': 'en-US-ChristopherNeural', 'rate': '-12%', 'pitch': '+0Hz', 'style': 'normal'},
    ],
    'swahili': [
        {'mood': 'peaceful',  'voice': 'puter:gemini:Puck',      'rate': '-5%', 'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'hopeful',   'voice': 'puter:gemini:Puck',      'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'emotional', 'voice': 'puter:gemini:Aoede',     'rate': '-5%', 'pitch': '+0Hz', 'style': 'normal'},
    ],
    'swahili_motivational': [
        {'mood': 'powerful',  'voice': 'puter:gemini:Zephyr',    'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'cinematic', 'voice': 'puter:gemini:Zephyr',    'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'energetic', 'voice': 'puter:gemini:Aoede',     'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
    ],
    'swahili_life': [
        {'mood': 'peaceful',  'voice': 'puter:gemini:Puck',      'rate': '-5%', 'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'hopeful',   'voice': 'puter:gemini:Puck',      'rate': '-5%',  'pitch': '+0Hz', 'style': 'normal'},
        {'mood': 'cinematic', 'voice': 'puter:gemini:Aoede',     'rate': '-5%', 'pitch': '+0Hz', 'style': 'normal'},
    ]
}

VIRAL_HOOKS = [
    'God told me to post this for someone specific tonight',
    'If you see this it was meant for you to find',
    'Stop scrolling this is your sign from God',
    'You were chosen to hear this today',
    'Heaven is sending you this message right now',
    'Do not scroll past without saying Amen',
]

CTA_TEMPLATES = [
    'Type AMEN if you needed to hear this today',
    'Comment YES if you receive this word',
    'Tag someone who needs this prayer right now',
    'Share this if it spoke to your spirit',
    'Comment 1 if you believe Comment 2 if you need a miracle',
    'Save this and watch it again tomorrow morning',
    'Drop a fire emoji if you are claiming this',
    'Type your name below and I will pray for you',
    'Comment your prayer request below',
    'Share this with one person who needs God today',
]

SWAHILI_CTA_TEMPLATES = [
    "Andika AMINA kama ulihitaji ujumbe huu",
    "Mtag mtu anayehitaji sala hii",
    "Mtumie rafiki anayehitaji Mungu leo",
    "Andika NDIO kama unaamini",
    "Hifadhi ujumbe huu kwa muda mgumu",
    "Andika 1 kama unaamini, Andika 2 kama unahitaji muujiza",
    "Andika jina lako nikuombee",
    "Andika ombi lako hapa chini",
]

SERIES_TEMPLATES = {
    'armor_of_god': {
        'name': 'The Armor of God',
        'parts': 7,
        'topics': [
            'The Belt of Truth that exposes every lie',
            'The Breastplate of Righteousness that guards your heart',
            'The Shoes of Peace that crush the enemy',
            'The Shield of Faith that blocks fiery darts',
            'The Helmet of Salvation that protects your mind',
            'The Sword of the Spirit that defeats darkness',
            'The Prayer that activates all the armor',
        ]
    },
    'powerful_prayers': {
        'name': 'Daily Power Prayers',
        'parts': 7,
        'topics': [
            'Day 1: A surrender prayer that changes everything',
            'Day 2: A breakthrough prayer for your impossible',
            'Day 3: A healing prayer for body and soul',
            'Day 4: A protection prayer for your family',
            'Day 5: A provision prayer for your finances',
            'Day 6: A peace prayer for your anxious heart',
            'Day 7: A thanksgiving prayer that opens heaven',
        ]
    },
}

SERIES_PROGRESS_FILE = Path('output/.series_progress.json')

def get_next_series_part(key):
    progress = {}
    if SERIES_PROGRESS_FILE.exists():
        try: progress = json.loads(SERIES_PROGRESS_FILE.read_text(encoding='utf-8'))
        except: pass
    current = progress.get(key, 0)
    series = SERIES_TEMPLATES.get(key)
    if not series: return None
    if current >= series['parts']: current = 0
    progress[key] = current + 1
    SERIES_PROGRESS_FILE.parent.mkdir(exist_ok=True, parents=True)
    SERIES_PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding='utf-8')
    return {
        'series_name': series['name'],
        'part_number': current + 1,
        'total_parts': series['parts'],
        'topic': series['topics'][current],
    }

def build_prompt(niche, topic, mood='peaceful', viral_hook=None, series_info=None, cta=None, language='english'):
    if niche == 'swahili' or language == 'swahili' or str(niche).startswith('swahili'):
        cta_sw = cta if cta else 'Andika AMINA kama ulihitaji ujumbe huu'
        return f'''Wewe ni mtengenezaji wa video za wima (Reels/Shorts) za kiroho na mafundisho ya Kikristo. Ujumbe wako unapaswa kuwa na mvuto mkubwa na hisia kali za kiimani.
Mada ya leo ni: "{topic}"

MISINGI YA MAANDISHI:
1. LAZIMA uandike kila kitu kwa KISWAHILI SAFISHI, ASILI, NA CHA KISASA CHA AFRIKA MASHARIKI.
2. EPUKA tafsiri za moja kwa moja (literal machine translation). Badala yake, tengeneza ujumbe wenye mtiririko mzuri kama mahubiri halisi ya Kiswahili ya kiroho (Kiswahili cha Kikanisa/Kiroho).
3. Tumia maneno ya kiroho kama: Imani thabiti, Neema, Ushindi dhidi ya majaribu, Ukombozi, Mwenyezi Mungu, Simba, Dhoruba, Baraka.
4. HAKUNA Kiingereza kabisa kwenye maneno ya kusomwa (bila code-switching).

MUUNDO WA MISTARI 7 HASA (si zaidi, si pungufu):
- Mstari 1 (Ndoano/Hook): Swali au tamko zito la kuvutia usikivu (maneno 4-8)
- Mistari 2-6 (Mwili): Ujumbe wa kiroho, mafundisho, au hamasa, mstari kwa mstari (maneno 4-8 kila mstari)
- Mstari 7 (Wito/CTA): Wito wa kuchukua hatua kama kuandika Amina au kushiriki (maneno 5-8)

SHERIA ZA ZIADA:
- HAKUNA namba (no numbering), HAKUNA alama za risasi (no bullets), HAKUNA narrator/body/cta labels
- HAKUNA alama za nukuu kuzunguka mistari (no quotation marks around lines)
- Weka emoji 1-2 zinazofaa mwanzoni au katikati ya kila mstari.
- LAZIMA: Mwishoni mwa kila mstari, weka mabano yaliyo na maneno 2-3 ya utafutaji wa video ya b-roll kwa Kiingereza (mfano: "(praying hands, divine light)") ijifungue ili tuyatumie kutafuta stock video kwenye Pexels/Pinterest.

MIFANO MIWILI YA MTINDO NA FORMAT INAYOTAKIWA (Follow this exact style):

MFANO A:
Je, unajua siri ya ushindi wa Daudi dhidi ya Goliath? 👑 (young shepherd boy, big giant)
Mungu haangalii urefu wala nguvu zako za mwili 💪 (strong man muscle, spiritual strength)
Yeye huangalia moyo safi na imani thabiti pekee ❤️ (folded praying hands, glowing light)
Usiogope ukubwa wa changamoto iliyo mbele yako leo 🛡️ (dark stormy sea, standing firm)
Mungu aliyeshinda jana, ndiye atakayekupigania leo pia ⚔️ (glowing cross, heavenly rays)
Weka tumaini lako lote kwake naye atatenda muujiza ✨ (sunrise mountain, open bible)
Andika AMINA kama unaamini Mungu atashinda vita yako leo 🙏 (hopeful look sky, peaceful sunset)

MFANO B:
Je, unapitia kwenye shimo la simba kama Danieli? 🦁 (lions in dark den, brave man)
Wakati maadui wanapopanga njama za kukuangamiza usiku kucha 🌌 (whispering shadows, ticking clock)
Kumbuka Mungu yuko hai na anakuona kila wakati 👀 (heavenly light beam, open bible)
Atafunga vinywa vya simba wanaotaka kukururarura 🛡️ (closed lion mouth, shield of light)
Imani yako thabiti ndiyo silaha yako ya pekee 💪 (praying hands, glowing cross)
Utatoka salama na kwa ushindi mkubwa wa ajabu 🌟 (sunrise through clouds, happy expression)
Andika AMINA na umtag mtu anayepitia jaribu ngumu leo 🙏 (folded hands praying, smiling friend)

Sasa tengeneza script kwa ajili ya mada ya "{topic}" kwa kutumia format hiyo hiyo ya mistari 7 hasa na mabano ya keywords za b-roll kwa Kiingereza mwishoni:'''

    cta_line = cta or random.choice(CTA_TEMPLATES)
    hook_instruction = ''
    if viral_hook:
        hook_instruction = f'IMPORTANT: Your FIRST line must be exactly: "{viral_hook}"\n\n'

    series_instruction = ''
    if series_info:
        series_instruction = f'''
This is PART {series_info['part_number']} of {series_info['total_parts']} in a series called "{series_info['series_name']}".
End with: "Part {series_info['part_number']+1 if series_info['part_number'] < series_info['total_parts'] else 1} drops tomorrow follow so you do not miss it"
'''

    niche_role = {
        'gospel': 'You are a powerful gospel content creator who reveals deep truths from the Bible.',
        'prayer': 'You are a prayer warrior who writes prayers that move heaven.',
        'bedtime_prayer': 'You are writing gentle whispered prayers for someone falling asleep.',
        'praise': 'You are a worship leader who teaches the power of praise.',
        'motivational': 'You are a brutal but loving life coach who tells hard truths.',
    }.get(niche, 'You are a content creator.')

    return f'''{niche_role}

Topic: {topic}

{hook_instruction}{series_instruction}
WRITE A 25-30 SECOND REEL SCRIPT WITH REAL VALUE:

STRUCTURE (8 lines total):
- Line 1: A SHOCKING hook (question, bold statement, or surprising truth)
- Lines 2-7: SPECIFIC content - tell a story, share a verse, reveal a truth, or teach something new (each line UNIQUE, no repeats)
- Line 8: CTA EXACTLY like this: "{cta_line}" (ONCE, do not repeat it)

RULES YOU MUST FOLLOW:
- Do NOT write generic phrases like "God loves you" or "trust God"
- DO include SPECIFIC details: Bible characters, exact verses, real stories
- Each line is ONE complete short thought (5-9 words max)
- Tone: {mood}, emotional, real
- EMOJIS: Include 1-2 contextually relevant emojis (e.g. 🙏, ✨, 😢, 👑, 🔥, 📖) in every line to make the captions visually engaging and look like a premium edited video.
- IMPORTANT: At the end of every single line, you MUST append a list of 2-3 visual search keywords inside parentheses representing the visual context for that specific line. Choose concrete search keywords (e.g. nouns, settings, actions) suitable for stock video searching (e.g. "David praying", "dark cave", "stormy sea", "divine light", "praying hands").

Format each line exactly like this:
The spoken line of text with emojis (search keyword 1, search keyword 2)

Return ONLY the script lines. No numbers. No labels. Just the lines with their parenthesized keywords.'''

@retry_async(max_attempts=3, base_delay=1.0)
async def generate_with_openai(prompt):
    import config.settings
    primary_key = getattr(config.settings, "OPENAI_API_KEY", "") or ENV.get("OPENAI_API_KEY", "") or OPENAI_API_KEY
    if not primary_key:
        raise Exception("No OpenAI API key configured")
    
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {primary_key}', 'Content-Type': 'application/json'}
    for model in ['gpt-4o-mini', 'gpt-4o']:
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You write viral spiritual reels that get massive engagement.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.95,
            'max_tokens': 450,
        }
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code == 200:
                    print(f'  OpenAI OK ({model})')
                    return r.json()['choices'][0]['message']['content']
                else:
                    print(f"  OpenAI key/model failed: OpenAI API status {r.status_code}: {r.text}. Trying next...")
        except Exception as e:
            print(f"  OpenAI error: {e}. Trying next...")
    raise Exception("OpenAI failed to generate script")

@retry_async(max_attempts=3, base_delay=1.0)
async def generate_with_cloudflare(prompt):
    import config.settings
    # Collect all available Cloudflare Workers AI credentials
    accounts = []
    
    # 1. Custom settings list
    custom_list = getattr(config.settings, "CLOUDFLARE_ACCOUNTS", [])
    if custom_list:
        accounts.extend(custom_list)
        
    # 2. Settings / env primary keys
    primary_id = getattr(config.settings, "CLOUDFLARE_ACCOUNT_ID", "") or ENV.get("CLOUDFLARE_ACCOUNT_ID", "") or CLOUDFLARE_ACCOUNT_ID
    primary_token = getattr(config.settings, "CLOUDFLARE_API_TOKEN", "") or ENV.get("CLOUDFLARE_API_TOKEN", "") or CLOUDFLARE_API_TOKEN
    if primary_id and primary_token:
        accounts.append({"account_id": primary_id, "api_token": primary_token})
        
    # 3. Built-in fallback credentials
    accounts.extend(CLOUDFLARE_BACKUP_ACCOUNTS)
    
    # Filter unique accounts while preserving order
    seen = set()
    unique_accounts = []
    for acct in accounts:
        aid = acct.get("account_id")
        tok = acct.get("api_token")
        if aid and tok and aid not in seen:
            seen.add(aid)
            unique_accounts.append(acct)
            
    if not unique_accounts:
        raise Exception("No Cloudflare Account ID or API Token configured")
        
    last_err = None
    # Iterate through each account
    for acct in unique_accounts:
        account_id = acct["account_id"]
        api_token = acct["api_token"]
        
        # Models to try (standard and backup)
        models = [
            "@cf/meta/llama-3.1-8b-instruct",
            "@cf/meta/llama-3-8b-instruct"
        ]
        
        for model in models:
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
            headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
            payload = {
                'messages': [
                    {'role': 'system', 'content': 'You write viral spiritual reels that get massive engagement.'},
                    {'role': 'user', 'content': prompt}
                ]
            }
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    r = await client.post(url, headers=headers, json=payload)
                    if r.status_code == 200:
                        res = r.json()
                        if res.get("success") and "result" in res:
                            print(f'  Cloudflare Workers AI OK (Account ID: ...{account_id[-6:]}, Model: {model})')
                            return res["result"].get("response", "")
                        else:
                            last_err = Exception(f"Cloudflare success=False or missing result: {r.text}")
                    else:
                        last_err = Exception(f"Cloudflare Workers AI status {r.status_code}: {r.text}")
            except Exception as e:
                last_err = e
                print(f"  Cloudflare error on account ...{account_id[-6:]} ({model}): {e}")
                
    # If all accounts failed, raise the last error
    raise last_err or Exception("All Cloudflare Workers AI accounts failed to generate script")

async def generate_with_groq(prompt):
    import config.settings
    keys = getattr(config.settings, "GROQ_KEYS", [])
    primary_key = getattr(config.settings, "GROQ_API_KEY", "") or GROQ_API_KEY
    key_list = keys if keys else ([primary_key] if primary_key else [])
    if not key_list:
        raise Exception("No Groq API keys configured")
    
    url = 'https://api.groq.com/openai/v1/chat/completions'
    last_err = None
    
    # Try up to 4 keys (we now have a 10-key pool, rotate through them)
    for key in key_list[:4]:
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
        for model in ['groq/compound-mini', 'qwen/qwen3.6-27b', 'groq/compound', 'openai/gpt-oss-20b']:
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'You write viral spiritual reels that get massive engagement.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.95,
                'max_tokens': 400,
            }
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    r = await client.post(url, headers=headers, json=payload)
                    if r.status_code == 200:
                        print(f'  Groq OK ({model})')
                        return r.json()['choices'][0]['message']['content']
                    else:
                        last_err = Exception(f"Groq API status {r.status_code}: {r.text[:100]}")
                        print(f"  Groq notice: {last_err}")
            except Exception as e:
                last_err = e
                print(f"  Groq connection notice: {e}")
                if "getaddrinfo" in str(e) or "ConnectError" in str(e):
                    raise last_err
    raise last_err or Exception("Groq failed to generate script")

async def generate_with_gemini(prompt):
    """Generate text using Gemini API.
    Supports both AQ.* Auth Keys (x-goog-api-key header) and AIzaSy* Standard keys (?key= param).
    Tries AQ.* keys first since they have higher quota and are the new default.
    """
    import config.settings
    env_keys = getattr(config.settings, "GEMINI_KEYS", []) or GEMINI_KEYS
    primary_key = getattr(config.settings, "GEMINI_API_KEY", "") or GEMINI_API_KEY

    # Sort: AQ.* auth keys first, then AIzaSy* standard keys
    auth_keys = [k for k in env_keys if k.startswith("AQ.")]
    standard_keys = [k for k in env_keys if k.startswith("AIzaSy")]
    if primary_key and primary_key not in standard_keys:
        standard_keys.insert(0, primary_key)
    key_list = auth_keys + standard_keys
    if not key_list:
        raise Exception("No Gemini API keys configured")

    last_err = None
    for key in key_list[:5]:  # Try up to 5 keys
        is_auth_key = key.startswith("AQ.")
        for model in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
            if is_auth_key:
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
                extra_headers = {'x-goog-api-key': key}
            else:
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
                extra_headers = {}
            payload = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'temperature': 0.95, 'maxOutputTokens': 450}}
            headers = {'Content-Type': 'application/json', **extra_headers}
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.post(url, headers=headers, json=payload)
                    if r.status_code == 200:
                        key_tag = 'Auth' if is_auth_key else 'Std'
                        print(f'  Gemini OK ({model}, {key_tag})')
                        return r.json()['candidates'][0]['content']['parts'][0]['text']
                    else:
                        last_err = Exception(f"Gemini API {r.status_code}: {r.text[:100]}")
            except Exception as e:
                last_err = e
                if "getaddrinfo" in str(e) or "ConnectError" in str(e):
                    raise last_err
    raise last_err or Exception("Gemini failed to generate script")


async def verify_swahili_content_with_gemini(text):
    """Uses Gemini API to verify and polish Swahili script/lyrics grammar, rhythm, and biblical accuracy."""
    prompt = f"""You are an expert East African Swahili songwriter and biblical scholar.
Please review, refine, and verify the following Swahili lyrics or script:

TEXT TO VERIFY:
\"\"\"
{text}
\"\"\"

INSTRUCTIONS:
1. Ensure fluent, natural East African Swahili (Swahili Sanifu).
2. Maintain inspirational, uplifting gospel tone.
3. Keep lines rhythmic and concise for 20-30s reel spoken delivery.
4. Output valid JSON in this exact structure:
{{
  "is_valid": true,
  "verified_swahili_text": "Refined Swahili lines here...",
  "feedback": "Short critique or confirmation..."
}}
Return ONLY the raw JSON block without markdown backticks.
"""
    try:
        raw_res = await generate_with_gemini(prompt)
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            clean_json = match.group(0)
            data = json.loads(clean_json)
            return data
        else:
            raise Exception("No JSON object found in response")
    except Exception as e:
        print(f"Gemini Swahili verification fallback: {e}")
        return {
            "is_valid": True,
            "verified_swahili_text": text,
            "feedback": "Bypassed verification (using original text)."
        }

async def generate_with_openrouter(prompt):
    import config.settings
    keys = getattr(config.settings, "OPENROUTER_KEYS", [])
    primary_key = getattr(config.settings, "OPENROUTER_API_KEY", "") or OPENROUTER_API_KEY
    # Build pool: all keys from OPENROUTER_KEYS + primary if not already present
    merged = list(keys) if keys else []
    if primary_key and primary_key not in merged:
        merged.insert(0, primary_key)
    if not merged:
        raise Exception("No OpenRouter API keys configured")

    url = 'https://openrouter.ai/api/v1/chat/completions'
    models = [
        'google/gemini-2.5-flash',
        'deepseek/deepseek-chat',
        'meta-llama/llama-3.1-8b-instruct:free',
        'mistralai/mistral-small-24b-instruct-2501:free'
    ]

    last_err = None
    for key in merged[:4]:  # Try up to 4 keys
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
        for model in models:
            payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.95, 'max_tokens': 450}
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.post(url, headers=headers, json=payload)
                    if r.status_code == 200:
                        print(f'  OpenRouter OK ({model})')
                        return r.json()['choices'][0]['message']['content']
                    else:
                        last_err = Exception(f"OpenRouter API status {r.status_code}: {r.text[:100]}")
            except Exception as e:
                last_err = e
                if "getaddrinfo" in str(e) or "ConnectError" in str(e):
                    raise last_err
    raise last_err or Exception("OpenRouter failed to generate script")

async def generate_with_ollama(prompt):
    import config.settings
    api_base = getattr(config.settings, "OLLAMA_API_BASE", "http://localhost:11434/v1")
    model = getattr(config.settings, "OLLAMA_MODEL", "llama3.2")
    keys = getattr(config.settings, "OLLAMA_KEYS", [])
    
    key_list = keys if keys else [""]
    
    url = f"{api_base.rstrip('/')}/chat/completions"
    
    for key in key_list:
        headers = {'Content-Type': 'application/json'}
        if key:
            headers['Authorization'] = f'Bearer {key}'
            
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You write viral spiritual reels that get massive engagement.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.95,
            'max_tokens': 400,
        }
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code == 200:
                    print(f'  Ollama OK ({model})')
                    return r.json()['choices'][0]['message']['content']
                elif r.status_code in [401, 403, 429]:
                    print(f'  Ollama key error status {r.status_code}, trying next key...')
        except Exception as e:
            print(f'  Ollama error: {e}')
    return None

_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)
_UNCLOSED_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*$", re.IGNORECASE | re.DOTALL)

def clean_ai_output(text):
    if not text: return []
    
    # Strip thinking blocks from reasoning models (e.g. DeepSeek-R1, Gemini 2.0 Thinking)
    text = _THINK_BLOCK_RE.sub("", text)
    text = _UNCLOSED_THINK_BLOCK_RE.sub("", text).strip()
    
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 3: continue
        while '[' in line and ']' in line:
            s, e = line.find('['), line.find(']')
            if e > s: line = (line[:s] + line[e+1:]).strip()
            else: break
        lower = line.lower()
        for prefix in ['narrator:', 'voice:', 'hook:', 'body:', 'cta:', 'line 1:', 'line 2:', 'line 3:', 'line 4:', 'line 5:', 'line 6:', 'line 7:', 'line 8:', 'line 9:', 'ndoano:', 'mwili:', 'wito:']:
            if lower.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        while line and line[0] in '0123456789.-*':
            if line[0].isdigit() and len(line) > 1 and line[1] in ').:':
                line = line[2:].strip()
            elif line[0] in '-*':
                line = line[1:].strip()
            else: break
        # Strip markdown bold/italic/heading markers that leak into final output
        line = re.sub(r'^#{1,6}\s*', '', line)    # ## Heading markers
        line = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', line)  # **bold** / *italic*
        line = line.strip('"').strip(chr(39)).strip('*').strip('#').strip()
        if len(line) >= 3:
            lines.append(line)
    return lines

def parse_line_keywords(line):
    line = line.strip()
    if '(' in line and line.endswith(')'):
        idx = line.rfind('(')
        spoken_text = line[:idx].strip()
        keywords_str = line[idx+1:-1].strip()
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        return spoken_text, keywords
    return line, []

SWAHILI_COMMON_ENGLISH_LEAK = [
    "the", "and", "you", "your", "with", "that", "this",
    "have", "will", "not", "for", "are", "from", "they",
    "god", "faith", "love", "life", "hope", "strength"
]

def validate_swahili_quality(lines: list) -> bool:
    if not lines:
        return False
    # Strip b-roll keywords inside parentheses first before language check
    cleaned_spoken_lines = []
    for line in lines:
        spoken_text, _ = parse_line_keywords(line)
        cleaned_spoken_lines.append(spoken_text)
        
    all_words = " ".join(cleaned_spoken_lines).lower().split()
    if not all_words:
        return False
    english_count = sum(1 for word in all_words if word in SWAHILI_COMMON_ENGLISH_LEAK)
    # If more than 15% of words are common English words, it failed
    threshold = len(all_words) * 0.15
    if english_count > threshold:
        print(f"  [Validator] ⚠️ Script quality check FAILED — detected {english_count} English words in Swahili script ({english_count/len(all_words)*100:.1f}%)")
        return False
    return True

class AIScriptGenerator:

    def __init__(self):
        import config.settings
        self.has_groq = bool(GROQ_API_KEY or getattr(config.settings, "GROQ_KEYS", []))
        self.has_gemini = bool(GEMINI_API_KEY)
        self.has_openrouter = bool(OPENROUTER_API_KEY or getattr(config.settings, "OPENROUTER_KEYS", []))
        self.has_ollama = bool(getattr(config.settings, "OLLAMA_API_BASE", "") or getattr(config.settings, "OLLAMA_KEYS", []))
        self.has_openai = bool(OPENAI_API_KEY or getattr(config.settings, "OPENAI_API_KEY", ""))
        self.has_cloudflare = bool(CLOUDFLARE_ACCOUNT_ID or getattr(config.settings, "CLOUDFLARE_ACCOUNT_ID", ""))
        
        avail = []
        if self.has_openai: avail.append('OpenAI')
        if self.has_cloudflare: avail.append('Cloudflare')
        if self.has_groq: avail.append('Groq')
        if self.has_gemini: avail.append('Gemini')
        if self.has_openrouter: avail.append('OpenRouter')
        if self.has_ollama: avail.append('Ollama')
        print(f'AI providers: {avail if avail else "local templates only"}')

    def pick_fresh_topic(self, niche):
        # Load fresh pools from settings if possible
        try:
            from config.settings import TOPIC_POOLS as settings_pools, NICHE_CONFIG as settings_niche
            pool_key = settings_niche.get(niche, {}).get("topic_pool_key", niche)
            topics = settings_pools.get(pool_key, settings_pools.get(niche, TOPIC_POOLS.get(niche, TOPIC_POOLS['gospel'])))
        except:
            topics = TOPIC_POOLS.get(niche, TOPIC_POOLS['gospel'])

        history = load_history()
        used = history.get(niche, [])
        fresh = [t for t in topics if t not in used[-15:]]
        if not fresh:
            fresh = topics
            history[niche] = []
        topic = random.choice(fresh)
        history.setdefault(niche, []).append(topic)
        history[niche] = history[niche][-30:]
        save_history(history)
        return topic

    def pick_mood_variant(self, niche, language='english'):
        if language == 'swahili' or str(niche).startswith('swahili'):
            # Fallback check for settings niches
            if niche in MOOD_VARIANTS:
                return random.choice(MOOD_VARIANTS[niche])
            return random.choice(MOOD_VARIANTS['swahili'])
        return random.choice(MOOD_VARIANTS.get(niche, MOOD_VARIANTS['gospel']))

    def pick_viral_hook(self, language='english', chance=0.4):
        if random.random() > chance: return None
        return random.choice(VIRAL_HOOKS) if language != 'swahili' else None

    def pick_cta(self, language='english'):
        if language == 'swahili':
            return random.choice(SWAHILI_CTA_TEMPLATES)
        return random.choice(CTA_TEMPLATES)

    async def generate_caption(self, script_data, niche='gospel'):
        title = script_data.get('title', '')
        hook = script_data.get('hook', '')
        body = ' '.join(script_data.get('body', []))
        cta = script_data.get('cta', '')
        
        prompt = f"""
You are an expert short-form video copywriter.
Analyze the following script title and content, and generate a highly engaging, viral description/caption for platforms like YouTube Shorts, TikTok, and Instagram Reels in the '{niche}' niche.

Video Title: "{title}"
Script Content:
"{hook} {body} {cta}"

Instructions:
1. Write a short, hooky, and compelling summary or quote (1-2 sentences).
2. Add a strong Call to Action.
3. Use relevant, engaging emojis.
4. Add 5-7 trending, relevant hashtags (including general tags like #shorts, #viral, and niche-specific ones).
5. Do not include any JSON brackets or metadata. Just output the final polished caption directly.

Return ONLY the caption text.
"""
        raw = None
        # Route caption generation as well: Swahili -> Gemini first, English -> Groq first
        is_sw = (niche == 'swahili' or script_data.get('language') == 'swahili' or str(niche).startswith('swahili'))
        if is_sw:
            if self.has_openai: raw = await generate_with_openai(prompt)
            if not raw and self.has_gemini: raw = await generate_with_gemini(prompt)
            if not raw and self.has_groq: raw = await generate_with_groq(prompt)
        else:
            if self.has_openai: raw = await generate_with_openai(prompt)
            if not raw and self.has_groq: raw = await generate_with_groq(prompt)
            if not raw and self.has_gemini: raw = await generate_with_gemini(prompt)
            
        if not raw and self.has_openrouter:
            raw = await generate_with_openrouter(prompt)
        if not raw and self.has_cloudflare:
            raw = await generate_with_cloudflare(prompt)
        
        if raw:
            return raw.strip().strip('"').strip("'").strip()
        else:
            tags = f"#shorts #viral #reels #{niche}"
            if niche in ['gospel', 'prayer', 'praise']:
                tags += " #faith #dailydevotion #bibletruth"
            elif is_sw:
                tags += " #imani #maombi #nenolaleo #kiswahili #injili"
            return f"{title}\n\n{tags}"

    async def generate(self, niche='gospel', topic=None, language='english',
                       use_viral_hook=True, series=None, time_based=False,
                       target_duration=None):

        if time_based:
            ctx = get_time_context()
            time_niches = TIME_NICHE_MAP.get(ctx, ['gospel'])
            niche = random.choice(time_niches)
            print(f'  Time: {ctx} -> {niche}')

        series_info = None
        if series:
            series_info = get_next_series_part(series)
            if series_info:
                topic = series_info['topic']
                print(f'  Series: {series_info["series_name"]} Part {series_info["part_number"]}/{series_info["total_parts"]}')

        if not topic:
            topic = self.pick_fresh_topic(niche)

        variant = self.pick_mood_variant(niche, language)
        mood = variant['mood']

        # Determine language routing
        is_swahili = (language == 'swahili' or niche == 'swahili' or str(niche).startswith('swahili'))
        actual_lang = 'swahili' if is_swahili else 'english'

        viral = None
        if use_viral_hook:
            viral = self.pick_viral_hook(language=actual_lang)
            if viral: print(f'  Viral hook: {viral}')

        cta = self.pick_cta(language=actual_lang)

        print(f'  Niche:     {niche}')
        print(f'  Language:  {actual_lang}')
        print(f'  Topic:     {topic}')
        print(f'  Mood:      {mood}')
        print(f'  Voice:     {variant["voice"]} (rate {variant["rate"]})')
        print(f'  CTA:       {cta}')

        prompt = build_prompt(niche, topic, mood, viral_hook=viral, series_info=series_info, cta=cta, language=actual_lang)

        # Optional word-budget so narration reels respect --duration
        if target_duration:
            try:
                budget_words = int(float(target_duration) * 2.6)
            except (TypeError, ValueError):
                budget_words = 0
            if budget_words > 0:
                if actual_lang == 'swahili':
                    prompt += (
                        f"\n\nKIASI CHA MUDA: Jumla ya script iwe ≈ {int(target_duration)} "
                        f"sekunde (maneno ≈ {budget_words} yote pamoja na ndoano, mwili na wito). "
                        "Ukipita hayo, punguza mistari ya mwili."
                    )
                else:
                    prompt += (
                        f"\n\nDURATION BUDGET: Keep the TOTAL spoken script ≈ {int(target_duration)} "
                        f"seconds (about {budget_words} words including hook, body and CTA). "
                        "Trim body lines if you would exceed it."
                    )

        # Set up provider chains based on language
        # OpenAI -> Gemini -> Groq -> OpenRouter -> Cloudflare -> Ollama
        if is_swahili:
            providers = [
                ('openai', generate_with_openai),
                ('gemini', generate_with_gemini),
                ('groq', generate_with_groq),
                ('openrouter', generate_with_openrouter),
                ('cloudflare', generate_with_cloudflare),
                ('ollama', generate_with_ollama)
            ]
        else:
            providers = [
                ('openai', generate_with_openai),
                ('groq', generate_with_groq),
                ('gemini', generate_with_gemini),
                ('openrouter', generate_with_openrouter),
                ('cloudflare', generate_with_cloudflare),
                ('ollama', generate_with_ollama)
            ]

        raw = None
        success_provider = None
        
        for name, gen_func in providers:
            if name == 'openai' and not self.has_openai: continue
            if name == 'groq' and not self.has_groq: continue
            if name == 'gemini' and not self.has_gemini: continue
            if name == 'openrouter' and not self.has_openrouter: continue
            if name == 'cloudflare' and not self.has_cloudflare: continue
            if name == 'ollama' and not self.has_ollama: continue

            print(f"  Trying {name}...")
            try:
                res = await asyncio.wait_for(gen_func(prompt), timeout=12.0)
            except asyncio.TimeoutError:
                print(f"  {name} timed out after 12s. Trying next provider...")
                continue
            except Exception as ex:
                print(f"  {name} notice: {ex}. Trying next provider...")
                continue

            if res:
                lines = clean_ai_output(res)
                if len(lines) >= 4:
                    if is_swahili:
                        if validate_swahili_quality(lines):
                            raw = res
                            success_provider = name
                            break
                        else:
                            print(f"  [Generator] {name} Swahili quality check notice.")
                    else:
                        raw = res
                        success_provider = name
                        break

        if raw and success_provider:
            lines = clean_ai_output(raw)
            if len(lines) >= 4:
                if len(lines) > 10: lines = lines[:10]
                
                # Parse lines to separate text and keywords
                parsed_lines = []
                keywords_map = []
                for ln in lines:
                    txt, kw = parse_line_keywords(ln)
                    parsed_lines.append(txt)
                    keywords_map.append(kw)

                
                title = topic[:70].title()
                if series_info:
                    title = f'{series_info["series_name"]} - Part {series_info["part_number"]}'
                
                hook_text = parsed_lines[0]
                hook_kw = keywords_map[0]
                
                cta_text = parsed_lines[-1] if len(parsed_lines) > 1 else cta
                cta_kw = keywords_map[-1] if len(parsed_lines) > 1 else []
                
                body_text = parsed_lines[1:-1] if len(parsed_lines) > 2 else parsed_lines[1:]
                body_kw = keywords_map[1:-1] if len(parsed_lines) > 2 else keywords_map[1:]
                
                return {
                    'id': f'ai_{niche}_{datetime.now().strftime("%H%M%S")}',
                    'title': title,
                    'thumb': (series_info['series_name'].upper() if series_info else topic.upper())[:40],
                    'hook': hook_text,
                    'body': body_text,
                    'cta': cta_text,
                    'broll_keywords': {
                        'hook': hook_kw,
                        'body': body_kw,
                        'cta': cta_kw
                    },
                    'tags': [niche, 'reels'],
                    'mood': mood,
                    'voice': variant['voice'],
                    'rate': variant['rate'],
                    'pitch': variant['pitch'],
                    'style': variant['style'],
                    'duration_estimate': len(lines) * 3.0,
                    'ai_generated': True,
                    'series': series_info,
                    'viral_hook_used': viral,
                    'cta_used': cta,
                    'language': actual_lang,
                    'source': success_provider
                }

        # ── LOCAL FALLBACK ──────────────────────────────────────
        print(f"  [ScriptGen] [!] All AI providers failed or were skipped -- using local template fallback")
        if is_swahili:
            print('  Using local Swahili template fallback')
            try:
                from src.scripts.swahili_script import SwahiliScriptManager
                safe_niche = niche
                if safe_niche not in ["swahili", "swahili_motivational", "swahili_life"]:
                    safe_niche = "swahili"
                mgr = SwahiliScriptManager(niche=safe_niche)
                s = mgr.get_random_script()
                if s:
                    s.update({
                        'id': f'local_{niche}_{datetime.now().strftime("%H%M%S")}',
                        'mood': mood,
                        'voice': variant['voice'],
                        'rate': variant['rate'],
                        'pitch': variant['pitch'],
                        'style': variant['style'],
                        'ai_generated': False,
                        'language': 'swahili',
                        'source': 'local'
                    })
                    return s
            except Exception as e:
                print(f"  Failed to load local Swahili fallback: {e}")
        
        # English or General Fallback
        from src.scripts.gospel_script import ScriptManager
        safe = niche if niche in ['gospel','prayer','motivational','swahili'] else 'gospel'
        mgr = ScriptManager(niche=safe, language=actual_lang)
        s = mgr.get_random_script()
        if s:
            # Make sure all standard keys exist
            s.update({
                'mood': mood,
                'voice': variant['voice'],
                'rate': variant['rate'],
                'pitch': variant['pitch'],
                'style': variant['style'],
                'language': actual_lang,
                'source': 'local',
                'broll_keywords': s.get('broll_keywords', {
                    'hook': [], 'body': [[] for _ in s.get('body', [])], 'cta': []
                })
            })
        return s

if __name__ == '__main__':
    async def test():
        gen = AIScriptGenerator()
        print('\n--- TEST ---')
        s = await gen.generate(niche='gospel')
        if s:
            print(f'\nTitle: {s["title"]}')
            print(f'Hook:  {s["hook"]}')
            print('Body:')
            for line in s.get('body', []):
                print(f'  - {line}')
            print(f'CTA:   {s["cta"]}')
            print(f'Keywords: {s.get("broll_keywords")}')
    asyncio.run(test())
