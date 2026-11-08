"""
VideoFactory — Swahili Script Template Database
================================================
Hand-crafted Swahili scripts used as local fallback
when all AI providers fail or are rate-limited.

These scripts are written in natural East African Swahili —
not translated from English. Each one is tuned for
20-28 second spoken delivery and includes b-roll keywords.
"""

import random
from typing import Optional, List, Dict

SWAHILI_SCRIPT_DATABASE = {
    "swahili": [  # Swahili Gospel
        {
            "id": "sw_gospel_local_001",
            "title": "Mungu Hakusahau Ndoto Zako",
            "thumb": "MUNGU HAKUSAHAU\nNDOTO ZAKO",
            "hook": "Mungu hakusahau ndoto zako 🙏",
            "body": [
                "Anajua kila maumivu uliyoyapitia 😢",
                "Kila machozi yako ameyahifadhi kwenye chupa yake 🏺",
                "Wakati wake si wakati wako wa kibinadamu ⏳",
                "Lakini wakati wake daima ni sahihi na mzuri 🌟",
                "Subiri kwa imani bila kukata tamaa kabisa ✨",
            ],
            "cta": "Fuata kwa nguvu zaidi ya imani kila siku 👑",
            "broll_keywords": {
                "hook": ["thoughtful person", "praying silently"],
                "body": [
                    ["crying eyes", "sad person walking"],
                    ["water tears", "glowing jar"],
                    ["hourglass sand", "ticking clock"],
                    ["beautiful sunrise", "golden light"],
                    ["open bible", "mountain sunrise"]
                ],
                "cta": ["glowing cross", "hopeful look"]
            },
            "tags": ["injili", "mungu", "imani", "swahili", "gospel", "tanzania", "kenya"],
            "mood": "hopeful",
            "voice": "puter:gemini:Fenrir",
            "rate": "+0%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 24.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_002",
            "title": "Neema Yake Inatosha",
            "thumb": "NEEMA YAKE\nINATOSHA",
            "hook": "Neema yake inatosha kweli kweli 💖",
            "body": [
                "Hata katika giza lake bado anakupenda sana 🌌",
                "Hata wakati unahisi umepoteza kila kitu 💔",
                "Yeye bado yuko upande wako wakati wote 🛡️",
                "Hakuna nguvu inayoweza kukutenganisha naye 🔗",
                "Upendo wake una nguvu kuliko dhoruba yoyote 🌊",
            ],
            "cta": "Hifadhi ukumbusho huu wa upendo wa Mungu leo 🙌",
            "broll_keywords": {
                "hook": ["calm waters", "glowing cross"],
                "body": [
                    ["night sky star", "dark room light"],
                    ["broken glass", "sad reflection"],
                    ["shield protection", "walking in light"],
                    ["chain broken", "freedom sky"],
                    ["ocean storm", "lighthouse beam"]
                ],
                "cta": ["folded hands", "sun rays through clouds"]
            },
            "tags": ["injili", "neema", "upendo", "kristo", "swahili", "imani"],
            "mood": "peaceful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-5%",
            "pitch": "-1Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_003",
            "title": "Amani Ya Mungu",
            "thumb": "AMANI YA MUNGU\nIPITAYO AKILI",
            "hook": "Amani ya Mungu inazidi akili zote 🌊",
            "body": [
                "Wakati wasiwasi unakuzunguka kama mawimbi 🌀",
                "Wakati maisha yanakusumbua usiku kucha 🛌",
                "Mwambie Mungu kila kitu bila aibu yoyote 🗣️",
                "Yeye anasikiliza sala yako kwa upole na upendo 👂",
                "Na amani yake itakulinda moyo wako daima 💖",
            ],
            "cta": "Shiriki hii na mtu anayehitaji amani leo 🙏",
            "broll_keywords": {
                "hook": ["placid lake", "calm forest"],
                "body": [
                    ["whirlpool water", "stormy clouds"],
                    ["sleepless man night", "insomnia dark room"],
                    ["kneeling in prayer", "church altar"],
                    ["ear listening", "comforting friend"],
                    ["heart icon glow", "peaceful forest walk"]
                ],
                "cta": ["sharing message phone", "happy family sunset"]
            },
            "tags": ["amani", "sala", "wasiwasi", "injili", "mungu", "swahili"],
            "mood": "peaceful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-8%",
            "pitch": "-2Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_004",
            "title": "Daudi Alimshinda Goliati",
            "thumb": "SHINDA GOLIATI\nWAKO LEO",
            "hook": "Goliati alionekana mkubwa sana kwa jeshi ⚔️",
            "body": [
                "Lakini Daudi alimwona mdogo mbele ya Mungu 👦",
                "Jiwe moja tu lilibadilisha historia ya taifa 🪨",
                "Tatizo lako linakufanya uone vibaya na uogope 🌪️",
                "Lakini Mungu analiambia tatizo kuwa ni dogo mno 🔎",
                "Imani ndogo inaweza kusogeza milima yote ya maisha ⛰️",
            ],
            "cta": "Fuata ukurasa huu na upate nguvu kila siku 🛡️",
            "broll_keywords": {
                "hook": ["giant shadow", "ancient soldier sword"],
                "body": [
                    ["shepherd boy", "looking up courage"],
                    ["pebble stone sling", "impact ripple"],
                    ["storm cloud mountain", "frightened eyes"],
                    ["microscope focus", "small dot light"],
                    ["mountain peak clouds", "faith moving mountain"]
                ],
                "cta": ["knight shield", "sparkling sword light"]
            },
            "tags": ["daudi", "imani", "shujaa", "injili", "biblia", "nguvu"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "+2%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 24.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_005",
            "title": "Alfajiri Inakuja",
            "thumb": "ALFAJIRI\nINAKUJA",
            "hook": "Usiku wa giza hauwezi kudumu milele 🌌",
            "body": [
                "Machozi ya usiku yanaleta furaha asubuhi mpya 🌅",
                "Hata Yosefu alipita shimoni kama mtumwa kwanza 🕳️",
                "Kabla ya kufikia kasri lake kubwa la utawala 👑",
                "Maumivu yako ya sasa yana lengo zuri mbeleni 🎯",
                "Asubuhi mpya inaleta rehema mpya za Bwana tena ✨",
            ],
            "cta": "Subiri na utaona jinsi Mungu afanyavyo leo 🙌",
            "broll_keywords": {
                "hook": ["midnight sky stars", "dark forest night"],
                "body": [
                    ["dew drops leaf", "morning sun beam"],
                    ["mud pit deep hole", "sold captive chains"],
                    ["palace gold throne", "crown jewel light"],
                    ["target bullseye archery", "road map future"],
                    ["fresh dew flower", "rising sun orange"]
                ],
                "cta": ["folded hands looking up", "glowing horizon"]
            },
            "tags": ["alfajiri", "tumaini", "yosefu", "mungu", "swahili", "injili"],
            "mood": "hopeful",
            "voice": "puter:gemini:Fenrir",
            "rate": "+0%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 24.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_006",
            "title": "Ombi Lako Limesikika",
            "thumb": "OMBI LAKO\nLIMESIKIKA",
            "hook": "Ombi lako limesikika huko mbinguni ☁️",
            "body": [
                "Ingawa inaonekana kama hakuna kinachotokea chini 🌍",
                "Mungu yuko kazini hata katika kimya kikuu 🤫",
                "Malaika wako tayari wameshuka na majibu yako 👼",
                "Usiache kuomba hata kama dhoruba inaongezeka ⛈️",
                "Jibu lako liko njiani na litakufurahisha sana 🎉",
            ],
            "cta": "Andika AMINA kupokea jibu lako la sala Leo! 🙏",
            "broll_keywords": {
                "hook": ["clouds split sunlight", "heaven portal glow"],
                "body": [
                    ["dry desert ground", "seed planting dirt"],
                    ["silence deep forest", "watching night sky"],
                    ["angel wing glow", "falling shooting star"],
                    ["rain storm wind", "ship in storm"],
                    ["package delivery courier", "happy surprise jump"]
                ],
                "cta": ["typing message on phone", "happy family dinner"]
            },
            "tags": ["sala", "maombi", "majibu", "imani", "injili", "amina"],
            "mood": "hopeful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-3%",
            "pitch": "+1Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_007",
            "title": "Nguvu ya Sala ya Katikati ya Usiku",
            "thumb": "SALA YA\nUSIKU WA MANANE",
            "hook": "Je, unajua nguvu ya sala ya usiku wa manane? ⏰",
            "body": [
                "Wakati ulimwengu mzima ukiwa umelala fofofo 🛌",
                "Sauti yako inafika mbinguni moja kwa moja 🎯",
                "Hakuna vikwazo, hakuna usumbufu wa kelele 🤫",
                "Machozi yako usiku yanabadilisha hatima yako kesho 🌅",
                "Paulo na Sila waliomba usiku, milango ikafunguka 🔓",
            ],
            "cta": "Hifadhi video hii kwa maombi yako ya leo usiku 🌃",
            "broll_keywords": {
                "hook": ["wall clock ticking", "moonlight window shadow"],
                "body": [
                    ["sleeping room night", "city skyline night silent"],
                    ["laser beam sky", "praying man silhouette"],
                    ["empty room desk lamp", "quiet woods"],
                    ["pen writing journal", "teardrop falling on paper"],
                    ["jail cell bars breaking", "rusty chains fall"]
                ],
                "cta": ["bedroom pray bed", "saving video on phone"]
            },
            "tags": ["maombi", "usiku", "paulo na sila", "breakthrough", "injili"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "-5%",
            "pitch": "-2Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili"
        },
        {
            "id": "sw_gospel_local_008",
            "title": "Upendo wa Mungu Hauna Mwisho",
            "thumb": "UPENDO WA MUNGU\nHAUNA MWISHO",
            "hook": "Upendo wa Mungu hauna kikomo wala mwisho ❤️",
            "body": [
                "Hata unapoanguka, Yeye anakusaidia kuinuka tena 🤝",
                "Hukumu za watu zinakuumiza na kukuvunja moyo 🗣️",
                "Lakini macho ya Mungu yanaona thamani yako ya kweli 💎",
                "Wewe ni mwanawe mpendwa, usijidharau kamwe 👑",
                "Alikununua kwa damu ya thamani ya Yesu msalabani 🩸",
            ],
            "cta": "Type 'YESU NI BWANA' kama unajivunia upendo huu 🙌",
            "broll_keywords": {
                "hook": ["infinite symbol loop", "sun shining lake"],
                "body": [
                    ["hand pulling up fallen climber", "helping hand"],
                    ["whispering fingers pointing", "sad face girl head down"],
                    ["scanning diamond jewelry", "treasure chest glowing"],
                    ["king crown royal", "mirror smile reflection"],
                    ["wood cross sunset red", "red drop water ripple"]
                ],
                "cta": ["happy church praise", "worship concert hands up"]
            },
            "tags": ["upendo", "kristo", "msalaba", "injili", "amani", "thamani"],
            "mood": "emotional",
            "voice": "puter:gemini:Fenrir",
            "rate": "-6%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 27.0,
            "niche": "swahili"
        }
    ],
    "swahili_motivational": [
        {
            "id": "sw_motiv_local_001",
            "title": "Anza Sasa Hivi",
            "thumb": "ANZA\nSASA HIVI",
            "hook": "Acha kusubiri wakati mzuri, anza sasa! 🚀",
            "body": [
                "Wakati mzuri hautakuja kamwe, wewe ndiye unayeuleta 🛠️",
                "Hofu inakuambia subiri kidogo zaidi kesho ⏳",
                "Lakini mafanikio yanasema: Anza leo na ulichonacho 📦",
                "Hatua moja ndogo inaweza kubadilisha mwelekeo mzima 📈",
                "Mtu unayetaka kuwa kesho anajengwa leo hii 🧱",
            ],
            "cta": "Fuata kwa ukumbusho na hamasa za kila siku 🔔",
            "broll_keywords": {
                "hook": ["rocket launch lift off", "running shoes start line"],
                "body": [
                    ["man constructing house", "hammering wood board"],
                    ["scared face looking window", "sand running down glass"],
                    ["empty notebook desk", "starting code typing"],
                    ["hiking trail fork path", "compass pointing north"],
                    ["building brick wall foundation", "man reflection mirror suit"]
                ],
                "cta": ["bell icon ring notification", "scrolling through phone screen"]
            },
            "tags": ["mafanikio", "hamasa", "anza leo", "nidhamu", "maisha", "swahili"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "+5%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 23.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_002",
            "title": "Nidhamu Ndiyo Siri ya Mafanikio",
            "thumb": "NIDHAMU NDIO\nSIRI YA MAFANIKIO",
            "hook": "Nidhamu inashinda hamasa kila siku ya wiki 🏆",
            "body": [
                "Hamasa inakuja na kwenda kama upepo wa msimu 💨",
                "Lakini nidhamu inabaki hata ukiwa unahisi vibaya 🌧️",
                "Mtu mwenye mafanikio hakujengwa kwa usiku mmoja tu 🌌",
                "Alijengwa kwa siku elfu za kufanya kazi ngumu ya siri 🛠️",
                "Hata usiku wa giza hakusimama, yeye aliendelea tu 🚶",
            ],
            "cta": "Hifadhi video hii na ujiulize: Unafanya nini leo? 🤔",
            "broll_keywords": {
                "hook": ["gold trophy cup champion", "runner training heavy rain"],
                "body": [
                    ["blowing autumn leaves wind", "passing clouds timelapse"],
                    ["alarm clock 5am wake up", "gritting teeth effort workout"],
                    ["sparkling diamond polish", "speed paint sketch artist"],
                    ["writing code dark room computer", "sweat dripping floor math"],
                    ["man walking alone city night lamp", "determined walk silhouette"]
                ],
                "cta": ["bookmark save button app", "looking at watch clock"]
            },
            "tags": ["nidhamu", "siri", "kazi", "jasho", "hamasa", "swahili_motivation"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "+8%",
            "pitch": "-1Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_003",
            "title": "Wewe Wa Kesho Anaangalia Leo",
            "thumb": "WEWE WA KESHO\nANAANGALIA LEO",
            "hook": "Wewe wa kesho anaangalia unavyofanya leo 👁️",
            "body": [
                "Kila uamuzi unaoufanya sasa unabadilisha hatima yako 🛤️",
                "Starehe ya sasa inaweza kuwa inaua ndoto zako za juu 😴",
                "Kazi ngumu ya sasa inaumbia maisha yako ya kifahari 💎",
                "Chagua ugumu leo ili uchague urahisi kesho mbeleni ⚖️",
                "Ndoto kubwa hazihitaji maombi tu, zinahitaji jasho pia 💦",
            ],
            "cta": "Shiriki na rafiki mmoja anayehitaji kuamka leo 🗣️",
            "broll_keywords": {
                "hook": ["man looking future screen hologram", "stern eyes focus portrait"],
                "body": [
                    ["railway tracks diverging split", "writing sign check list"],
                    ["sleeping couch television remote", "clouds fading away sun"],
                    ["welding metal sparks", "office worker writing busy"],
                    ["weight lifting heavy barbell", "drinking cold water sweat"],
                    ["sketching layout blueprint design", "crying praying working hard"]
                ],
                "cta": ["shaping hand sharing link", "waking up friend shoulder pat"]
            },
            "tags": ["ndoto", "jasho", "uamuzi", "kesho", "swahili", "motisha"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "+6%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 24.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_004",
            "title": "Eneo La Starehe Ni Gereza",
            "thumb": "ENEO LA STAREHE\nNI GEREZA",
            "hook": "Eneo lako la starehe ni gereza la maendeleo 🚫",
            "body": [
                "Hakuna kitu kizuri kinachokua ukiwa umeridhika tu 🌱",
                "Maumivu ya kujaribu na kushindwa ni shule ya hekima 🏫",
                "Kila jaribio lililofeli linakuongezea nguvu mpya 💪",
                "Acha kuogopa kukataliwa au kuchekwa na watu wengine 🗣️",
                "Uthabiti ndiyo silaha kubwa kuliko talanta yoyote duniani 🛡️",
            ],
            "cta": "Gonga Like kama utakwenda kupambana leo! 🔥",
            "broll_keywords": {
                "hook": ["rusty cell bars", "closed cage bird lock"],
                "body": [
                    ["wilted plant dry ground", "green seedling sprout sun"],
                    ["man failing jump hurdle falling", "old scrolls books study library"],
                    ["battery charging green power", "bending iron steel bare hands"],
                    ["people laughing pointing mock", "man walking away proudly head high"],
                    ["shield blocking arrows defense", "sharpening sword grinding wheel"]
                ],
                "cta": ["pressing like heart button screen", "fist bump handshake agreement"]
            },
            "tags": ["starehe", "gereza", "jaribio", "uthabiti", "pambana", "motisha"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "+7%",
            "pitch": "-2Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_005",
            "title": "Usijieleze kwa Watu Wasiohusika",
            "thumb": "ACHA\nKUJIELEZA",
            "hook": "Acha kujieleza kwa watu wasiojali safari yako 🤫",
            "body": [
                "Kazi yako si kuwafanya waelewe, ni kufikia malengo yako 🎯",
                "Watu wengi wanataka kukuona ukishindwa ili wajisikie vizuri 📉",
                "Fanya kazi kwa siri kubwa, acha matokeo yapige kelele 🔊",
                "Moyo wako una jibu kuliko maoni mia moja ya mitandao 📱",
                "Wanaokuhukumu leo watakusalimia kwa heshima kesho kutwa 🤝",
            ],
            "cta": "Hifadhi ujumbe huu ili usisahau kusimama imara 🛡️",
            "broll_keywords": {
                "hook": ["finger on lips shh gesture", "walking away down quiet road"],
                "body": [
                    ["man checking off calendar target", "running up steps tower"],
                    ["sly smile face evil look", "graph going down red"],
                    ["whispering in dark room office", "champagne pop celebration crowd"],
                    ["heart icon glowing chest", "scrolling phone bad comments"],
                    ["critic point finger shame", "handshake formal bow respect suit"]
                ],
                "cta": ["saving post phone bookmark", "standing strong wind gust mountain"]
            },
            "tags": ["siri", "matokeo", "safari", "malengo", "kazi", "motisha"],
            "mood": "cinematic",
            "voice": "puter:gemini:Zephyr",
            "rate": "+2%",
            "pitch": "-2Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_006",
            "title": "Kazi kwa Akili na Nidhamu",
            "thumb": "KAZI KWA AKILI\nSI NGUVU TU",
            "hook": "Kazi ngumu bila akili ni utumwa wa hiari 🧠",
            "body": [
                "Punda anafanya kazi kila siku lakini hapati utajiri 🐴",
                "Jifunze kuongeza ujuzi wa thamani kubwa sokoni 📈",
                "Nenda hatua moja mbele ya wengine kwa kujisomea vitabu 📚",
                "Muda wako ndio mtaji mkubwa kuliko fedha zote za benki ⏳",
                "Siri ya matajiri si kufanya kazi, ni kuweka mifumo mizuri ⚙️",
            ],
            "cta": "Follow kujifunza siri za kifedha na nidhamu kila siku 📈",
            "broll_keywords": {
                "hook": ["man thinking logic puzzle board", "chained slave sand carrying"],
                "body": [
                    ["donkey pulling heavily loaded cart", "dirty coins dust hand"],
                    ["typing programming computer terminal", "trading charts green uptrend"],
                    ["reading books desk lamp pile", "man stepping up escalator stairs"],
                    ["hourglass sand running out gold", "bank vault door safe gold bar"],
                    ["gear rotating system machine", "business team meeting planning"]
                ],
                "cta": ["follow user screen click icon", "wealth growth tree seed sprout"]
            },
            "tags": ["akili", "utajiri", "ujuzi", "muda", "mifumo", "motisha"],
            "mood": "cinematic",
            "voice": "puter:gemini:Zephyr",
            "rate": "+5%",
            "pitch": "-1Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_007",
            "title": "Thamani ya Kujikubali",
            "thumb": "THAMANI YA\nKUJIKUBALI LEO",
            "hook": "Je, unajua thamani ya kujikubali ulivyo? 💎",
            "body": [
                "Kamwe usijilinganishe na picha za uongo za mitandaoni 📱",
                "Kila mtu ana vita anayopigana ambayo huwezi kuiona 🛡️",
                "Uzuri na uwezo wako uko kwenye upekee wako wa asili 🎨",
                "Kujipenda na kujisamehe ni hatua ya kwanza ya ushindi 💖",
                "Wewe si makosa yako ya jana, wewe ni uwezekano wa kesho 🌅",
            ],
            "cta": "Shiriki hii na mtu anayejisikia mnyonge leo 🤝",
            "broll_keywords": {
                "hook": ["gemstone diamond reflecting sun", "looking mirror smiling confident"],
                "body": [
                    ["scrolling fake filter photos phone", "looking depressed bed"],
                    ["shadow warrior shield battle", "sad office worker night desk"],
                    ["artist painting unique art brush", "nature bird flying sky alone"],
                    ["warm hug comforting hug self", "joyful walking meadow hands out"],
                    ["sunrise beach fresh breeze", "erasing blackboard chalk cleanup"]
                ],
                "cta": ["share button press app", "patting child back encouragement"]
            },
            "tags": ["thamani", "kujikubali", "upekee", "ushindi", "swahili_motisha"],
            "mood": "hopeful",
            "voice": "puter:gemini:Fenrir",
            "rate": "+0%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili_motivational"
        },
        {
            "id": "sw_motiv_local_008",
            "title": "Maumivu Yanatengeneza Nguvu",
            "thumb": "MAUMIVU YATAKUPA\nNGUVU MPYA LEO",
            "hook": "Maumivu unayohisi leo ndiyo nguvu ya kesho 💪",
            "body": [
                "Kila machozi unayomwaga yananywesha mbegu ya ujasiri 🌱",
                "Dhoruba haiji kukuharibu, inakuja kusafisha njia yako 🌪️",
                "Hakuna dhahabu inayong'aa bila kupita kwenye moto mkali 🔥",
                "Simama imara katikati ya dhoruba, wewe ni mshindi 🛡️",
                "Wakati mgumu unaisha lakini watu wagumu wanadumu daima 🧗",
            ],
            "cta": "Andika 'NIMESHINDA' kama uko tayari kuvuka dhoruba! 🙌",
            "broll_keywords": {
                "hook": ["crying man wipe tear head up", "muscle arm flex workout"],
                "body": [
                    ["water dropper on soil seed sprout", "brave stance chest out wind"],
                    ["thunder lightning heavy rain", "broom sweeping dirt floor path"],
                    ["smelting gold lava factory fire", "sparkling wedding ring glow"],
                    ["soldier standing shield arrows rain", "climbing steep rock mountain cliff"],
                    ["determined hiker reaching peak summit", "strong handshake mountain"]
                ],
                "cta": ["typing comment section app", "hands pointing heaven sunset sun"]
            },
            "tags": ["maumivu", "nguvu", "dhoruba", "dhahabu", "mshindi", "motisha"],
            "mood": "powerful",
            "voice": "puter:gemini:Zephyr",
            "rate": "+6%",
            "pitch": "+0Hz",
            "style": "normal",
            "duration_estimate": 25.0,
            "niche": "swahili_motivational"
        }
    ],
    "swahili_life": [
        {
            "id": "sw_life_local_001",
            "title": "Familia Ndiyo Utajiri wa Kweli",
            "thumb": "FAMILIA NDIO\nUTAJIRI WA KWELI",
            "hook": "Familia ndiyo utajiri wa kweli maishani 💖",
            "body": [
                "Fedha zinakuja na kwenda kama mwanga wa jua 💸",
                "Lakini familia ya kweli inabaki hata ukiwa kimya 🤫",
                "Mama alifanya mengi sana bila kupata shukrani stahiki 👩",
                "Baba aliamka mapema asubuhi bila kusema neno la malalamiko 👨",
                "Leo hii wapigie simu, usisahau asili yako ya nyumbani 📞",
            ],
            "cta": "Wapende familia yako kabla haijachelewa sana leo ⏳",
            "broll_keywords": {
                "hook": ["happy family group hug sunset", "kids playing village home"],
                "body": [
                    ["blowing bills money hand", "shadow dark room silhouette"],
                    ["dining table silent family", "cozy home warmth fireplace"],
                    ["african mother cooking firewood", "tired mother smiling baby"],
                    ["farmer waking up early fields dawn", "carrying wood logs back"],
                    ["calling phone dial mobile", "traditional old clay house village"]
                ],
                "cta": ["hourglass sand drop", "happy grandmother hugging child"]
            },
            "tags": ["familia", "utajiri", "wazazi", "mama", "baba", "hekima", "swahili_life"],
            "mood": "peaceful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-10%",
            "pitch": "-2Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili_life"
        },
        {
            "id": "sw_life_local_002",
            "title": "Heshima Inajengwa kwa Matendo",
            "thumb": "HESHIMA INAJENGWA\nKWA MATENDO YAKO",
            "hook": "Heshima inajengwa kwa matendo si kwa maneno 🤝",
            "body": [
                "Kinywa chako kinaweza kusema uwongo na ahadi nzuri 🗣️",
                "Lakini miguu yako na mikono yako daima zinasema ukweli 👣",
                "Mzee wa mtaa ana hekima zaidi kuliko kurasa elfu za kitabu 📚",
                "Sikiliza ushauri wa waliotangulia na upate salama ya safari 🚶",
                "Unyenyekevu ni ufunguo wa kufungua milango yote ya heshima 🔑",
            ],
            "cta": "Gonga Like kama unaamini heshima ni bora kuliko fedha 🙌",
            "broll_keywords": {
                "hook": ["shaking hands respect agreement", "man helping neighbor lift wood"],
                "body": [
                    ["whispering speaking gossip shadow", "written contract paper signature"],
                    ["steps walking on dust road", "clean hand working building brick"],
                    ["african old elder sitting under tree", "wrinkled hands holding cane staff"],
                    ["father advising son sunset field", "hiking path signs map forest"],
                    ["bowing head respectfully greeting", "gold key unlocking wooden chest lock"]
                ],
                "cta": ["heart like icon animation", "heap of gold coins bank vault"]
            },
            "tags": ["heshima", "matendo", "mzee", "hekima", "ushauri", "unyenyekevu"],
            "mood": "peaceful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-8%",
            "pitch": "-1Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili_life"
        },
        {
            "id": "sw_life_local_003",
            "title": "Subira Huvuta Heri Daima",
            "thumb": "SUBIRA HUVUTA HERI\nKAMA ASALI",
            "hook": "Subira huvuta heri kama asali ya mwituni 🍯",
            "body": [
                "Mambo mazuri huchukua muda mrefu kukomaa na kuwa matamu 🍇",
                "Usiwe na haraka ya kuvuna matunda yasiyoiva bado 🌳",
                "Kila mtu ana saa yake ya kukimbia na kuvuna kwake ⏳",
                "Kuchelewa kwako si kufeli, Mungu anakuepusha na ajali 🛡️",
                "Tulia na uamini mchakato wako wa maisha kwa amani 🧘",
            ],
            "cta": "Shiriki hii na mtu mwenye haraka ya mafanikio leo 🗣️",
            "broll_keywords": {
                "hook": ["honey dripping from honeycomb honeybee", "quiet river flowing through forest"],
                "body": [
                    ["green grape bunch growing sun", "red apple falling branch fruit"],
                    ["farmer looking green fields wheat", "eating unripe green mango bite sour"],
                    ["wall clock ticking fast time lapse", "wheat harvesting tractor farmer"],
                    ["car crash skid safety braking", "angel wing protecting shield overlay"],
                    ["yoga meditation breathing calm lake", "pottery shaping clay spinning wheel"]
                ],
                "cta": ["share button click app", "hustling crowd speed up traffic city"]
            },
            "tags": ["subira", "heri", "muda", "mchakato", "kufeli", "amani", "life"],
            "mood": "peaceful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-10%",
            "pitch": "-2Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili_life"
        },
        {
            "id": "sw_life_local_004",
            "title": "Fedha Inakuja Na Kwenda Tabia Inabaki",
            "thumb": "FEDHA INAKUJA\nTABIA INABAKI DAIMA",
            "hook": "Fedha inakuja na kwenda lakini tabia inabaki daima 🛡️",
            "body": [
                "Utajiri unaweza kupotea kwa dhoruba moja tu ya kesho 🌪️",
                "Lakini utu na wema wako vinajenga jina lisilofutika kamwe ✍️",
                "Rafiki wa kweli anajulikana wakati ukiwa huna kitu kabisa 💔",
                "Usimdharau yeyote ukiwa juu, utawaona ukiwa unashuka chini 📉",
                "Asili yako ndiyo nguvu yako, usisahau ulipotoka kamwe 🧱",
            ],
            "cta": "Hifadhi ukumbusho huu ili usipotee kwenye safari ya maisha 🙌",
            "broll_keywords": {
                "hook": ["burning dollar bill fire spark", "strong stone tower wind storm"],
                "body": [
                    ["empty safe box dust", "ocean waves crashing storm beach"],
                    ["giving bread to poor child hand", "gravestone engraved text name sunset"],
                    ["sad man sitting corner floor dark", "happy friends hugging walking rain"],
                    ["boss pointing shouting clerk office", "man falling down slide ladder"],
                    ["clay pot under mud wall", "dusty village road path forest"]
                ],
                "cta": ["app save bookmark phone", "hiking path sunset reaching peak"]
            },
            "tags": ["fedha", "tabia", "utu", "wema", "asili", "safari", "hekima"],
            "mood": "peaceful",
            "voice": "puter:gemini:Fenrir",
            "rate": "-8%",
            "pitch": "-1Hz",
            "style": "normal",
            "duration_estimate": 26.0,
            "niche": "swahili_life"
        }
    ]
}

class SwahiliScriptManager:
    """
    Manager for local Swahili template scripts.
    Used as the final fallback when AI generation fails.
    """
    def __init__(self, niche: str = "swahili"):
        self.niche = niche if niche in SWAHILI_SCRIPT_DATABASE else "swahili"
        self.scripts = SWAHILI_SCRIPT_DATABASE.get(self.niche, SWAHILI_SCRIPT_DATABASE["swahili"])

    def get_random_script(self, niche: Optional[str] = None) -> Dict:
        target_niche = niche if niche in SWAHILI_SCRIPT_DATABASE else self.niche
        scripts_list = SWAHILI_SCRIPT_DATABASE.get(target_niche, SWAHILI_SCRIPT_DATABASE["swahili"])
        script = random.choice(scripts_list)
        return script.copy()

    def get_script_by_id(self, script_id: str) -> Optional[Dict]:
        for category, scripts_list in SWAHILI_SCRIPT_DATABASE.items():
            for s in scripts_list:
                if s["id"] == script_id:
                    return s.copy()
        return None

    def get_all_scripts(self) -> List[Dict]:
        return self.scripts.copy()

    def get_full_text(self, script: Dict) -> str:
        lines = [script["hook"]] + script["body"] + [script["cta"]]
        return " ".join(lines)

    def get_lines(self, script: Dict) -> List[str]:
        return [script["hook"]] + script["body"] + [script["cta"]]
