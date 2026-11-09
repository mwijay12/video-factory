let currentConfig = {};
let currentScript = null;
let pollingInterval = null;
let pipelineInterval = null;

// Sidebar Collapse Toggle
function toggleSidebarCollapse() {
    const sidebar = document.getElementById("app-sidebar");
    const workspace = document.getElementById("app-workspace");
    const icon = document.getElementById("collapse-icon");
    if (!sidebar || !workspace) return;

    const isCollapsed = sidebar.classList.toggle("collapsed");
    workspace.classList.toggle("expanded", isCollapsed);

    if (icon) {
        icon.setAttribute("data-lucide", isCollapsed ? "panel-left-open" : "panel-left-close");
        if (typeof lucide !== "undefined") lucide.createIcons();
    }

    try {
        localStorage.setItem("videofactory_sidebar_collapsed", isCollapsed ? "1" : "0");
    } catch(e){}

    // GSAP micro-animation for smooth layout shift
    if (typeof gsap !== "undefined") {
        gsap.fromTo(workspace, { opacity: 0.88, y: 2 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" });
    }
}

// Restore sidebar state on load
document.addEventListener("DOMContentLoaded", () => {
    try {
        if (localStorage.getItem("videofactory_sidebar_collapsed") === "1") {
            const sidebar = document.getElementById("app-sidebar");
            const workspace = document.getElementById("app-workspace");
            if (sidebar && workspace) {
                sidebar.classList.add("collapsed");
                workspace.classList.add("expanded");
                const icon = document.getElementById("collapse-icon");
                if (icon) icon.setAttribute("data-lucide", "panel-left-open");
            }
        }
    } catch(e){}
    if (typeof lucide !== "undefined") lucide.createIcons();
});

        const PUTER_PROVIDERS_CONFIG = {
            'aws-polly': {
                voices: [
                    { value: 'Joanna', label: 'Joanna (Female)' },
                    { value: 'Matthew', label: 'Matthew (Male)' },
                    { value: 'Ivy', label: 'Ivy (Female)' },
                    { value: 'Justin', label: 'Justin (Male)' },
                    { value: 'Kendra', label: 'Kendra (Female)' },
                    { value: 'Kimberly', label: 'Kimberly (Female)' },
                    { value: 'Salli', label: 'Salli (Female)' },
                    { value: 'Joey', label: 'Joey (Male)' },
                    { value: 'Ruth', label: 'Ruth (Female)' },
                ],
                engines: [
                    { value: 'neural', label: 'Neural' },
                    { value: 'generative', label: 'Generative' },
                    { value: 'standard', label: 'Standard' },
                    { value: 'long-form', label: 'Long Form' }
                ],
                models: [ // Reused for languages
                    { value: 'en-US', label: 'English (US)' },
                    { value: 'en-GB', label: 'English (UK)' },
                    { value: 'es-US', label: 'Spanish (US)' },
                    { value: 'fr-FR', label: 'French' },
                    { value: 'de-DE', label: 'German' },
                    { value: 'it-IT', label: 'Italian' }
                ]
            },
            'openai': {
                voices: [
                    { value: 'alloy', label: 'Alloy' },
                    { value: 'ash', label: 'Ash' },
                    { value: 'ballad', label: 'Ballad' },
                    { value: 'coral', label: 'Coral' },
                    { value: 'echo', label: 'Echo' },
                    { value: 'fable', label: 'Fable' },
                    { value: 'nova', label: 'Nova' },
                    { value: 'onyx', label: 'Onyx' },
                    { value: 'sage', label: 'Sage' },
                    { value: 'shimmer', label: 'Shimmer' }
                ],
                models: [
                    { value: 'gpt-4o-mini-tts', label: 'GPT-4o Mini TTS' },
                    { value: 'tts-1', label: 'TTS-1' },
                    { value: 'tts-1-hd', label: 'TTS-1 HD' }
                ],
                formats: [
                    { value: 'mp3', label: 'MP3' },
                    { value: 'wav', label: 'WAV' },
                    { value: 'opus', label: 'Opus' },
                    { value: 'aac', label: 'AAC' }
                ]
            },
            'elevenlabs': {
                voices: [
                    { value: '21m00Tcm4TlvDq8ikWAM', label: 'Rachel (Sample)' },
                    { value: 'AZnzlk1XvdvUeBnXmlld', label: 'Domi' },
                    { value: 'EXAVITQu4vr3xnSDxMaL', label: 'Bella' },
                    { value: 'ODq5zmih8GrVes37Dizd', label: 'Patrick' },
                    { value: 'N2lVS1w4EtoT3dr4eOWO', label: 'Callum' }
                ],
                models: [
                    { value: 'eleven_multilingual_v2', label: 'Multilingual v2' },
                    { value: 'eleven_flash_v2_5', label: 'Flash v2.5' },
                    { value: 'eleven_turbo_v2_5', label: 'Turbo v2.5' }
                ],
                formats: [
                    { value: 'mp3_44100_128', label: 'MP3 128kbps' },
                    { value: 'pcm_16000', label: 'PCM 16kHz' }
                ]
            },
            'gemini': {
                voices: [
                    { value: 'Kore', label: 'Kore' },
                    { value: 'Zephyr', label: 'Zephyr' },
                    { value: 'Puck', label: 'Puck' },
                    { value: 'Charon', label: 'Charon' },
                    { value: 'Fenrir', label: 'Fenrir' },
                    { value: 'Leda', label: 'Leda' },
                    { value: 'Aoede', label: 'Aoede' },
                    { value: 'Enceladus', label: 'Enceladus' }
                ],
                models: [
                    { value: 'gemini-2.5-flash-preview-tts', label: 'Gemini 2.5 Flash' },
                    { value: 'gemini-2.5-pro-preview-tts', label: 'Gemini 2.5 Pro' }
                ]
            },
            'xai': {
                voices: [
                    { value: 'eve', label: 'Eve (Energetic)' },
                    { value: 'ara', label: 'Ara (Warm)' },
                    { value: 'rex', label: 'Rex (Confident)' },
                    { value: 'sal', label: 'Sal (Smooth)' },
                    { value: 'leo', label: 'Leo (Authoritative)' }
                ],
                models: [ // Reused for languages
                    { value: 'en', label: 'English' },
                    { value: 'auto', label: 'Auto-detect' }
                ],
                formats: [
                    { value: 'mp3', label: 'MP3' },
                    { value: 'wav', label: 'WAV' }
                ]
            }
        };

        // Track Puter connection state
        let puterConnected = false;

        // Initialize App
        async function init() {
            lucide.createIcons();
            await loadConfig();
            await loadSongs();
            await loadBrowserFolders();
            await loadPipelineConfig();
            await loadPipelineLogs();
            updateVoiceOptions();
            
            // Monitor Puter SDK connection status
            if (typeof puter !== 'undefined') {
                if (puter.auth && typeof puter.auth.isSignedIn === 'function') {
                    puterConnected = puter.auth.isSignedIn();
                }
                // Listen for connect/disconnect events
                if (puter.on) {
                    puter.on('connect', () => { puterConnected = true; console.log('Puter connected'); });
                    puter.on('disconnect', () => { puterConnected = false; console.warn('Puter disconnected'); });
                }
            }
            
            await autoSyncPuterToken();
        }

        // Fetch configurations from backend
        async function loadConfig() {
            try {
                let res = await fetch("/api/config");
                currentConfig = await res.json();
                
                // Niche choices update
                let nicheSel = document.getElementById("script-niche");
                let savedNiche = nicheSel ? nicheSel.value : null;
                
                if (nicheSel) {
                    nicheSel.innerHTML = "";
                    currentConfig.niches.forEach(n => {
                        let opt = document.createElement("option");
                        opt.value = n;
                        opt.textContent = n.charAt(0).toUpperCase() + n.slice(1) + " Reels";
                        nicheSel.appendChild(opt);
                    });
                    if (savedNiche && Array.from(nicheSel.options).some(o => o.value === savedNiche)) {
                        nicheSel.value = savedNiche;
                    }
                }
            } catch (e) {
                console.error("Failed to load config", e);
            }
        }

        // Fetch songs from backend
        async function loadSongs() {
            try {
                let res = await fetch("/api/songs/list");
                let data = await res.json();
                let musSel = document.getElementById("render-music");
                let bulkMusSel = document.getElementById("bulk-music");
                let lyricsSel = document.getElementById("lyrics-song");
                
                musSel.innerHTML = '<option value="auto_smart" selected>🎵 Auto-Select (Smart Niche Rotation)</option><option value="">None (Voice only)</option>';
                if (bulkMusSel) {
                    bulkMusSel.innerHTML = '<option value="auto_smart" selected>🎵 Auto-Select (Smart Niche Rotation)</option><option value="">None (Voice only)</option>';
                }
                if (lyricsSel) {
                    lyricsSel.innerHTML = '<option value="" disabled selected>Select song from assets...</option>';
                }
                
                data.songs.forEach(s => {
                    let opt = document.createElement("option");
                    opt.value = s.path;
                    opt.setAttribute("data-url", s.url);
                    opt.textContent = `[${s.category.toUpperCase()}] ${s.name}`;
                    musSel.appendChild(opt);
                    
                    if (bulkMusSel) {
                        let optBulk = opt.cloneNode(true);
                        bulkMusSel.appendChild(optBulk);
                    }
                    if (lyricsSel) {
                        let optLyrics = opt.cloneNode(true);
                        lyricsSel.appendChild(optLyrics);
                    }
                });
            } catch (e) {
                console.error("Failed to load songs", e);
            }
        }

        async function uploadCustomMusic(inputId, selectId, statusId) {
            let fileInput = document.getElementById(inputId);
            let statusSpan = document.getElementById(statusId);
            if (!fileInput.files || fileInput.files.length === 0) return;
            
            let file = fileInput.files[0];
            let formData = new FormData();
            formData.append("file", file);
            
            let originalText = statusSpan.textContent;
            statusSpan.textContent = "Uploading...";
            statusSpan.style.color = "var(--primary)";
            
            try {
                let res = await fetch("/api/songs/upload", {
                    method: "POST",
                    body: formData
                });
                
                if (!res.ok) {
                    let err = await res.json();
                    throw new Error(err.detail || "Upload failed");
                }
                
                let data = await res.json();
                statusSpan.textContent = "Uploaded!";
                statusSpan.style.color = "var(--accent-success)";
                
                // Reload all songs
                await loadSongs();
                
                // Auto-select the newly uploaded song
                let select = document.getElementById(selectId);
                if (select) {
                    select.value = data.song.path;
                    // Trigger change event to load preview URL etc if needed
                    select.dispatchEvent(new Event('change'));
                }
                
                setTimeout(() => {
                    statusSpan.textContent = originalText;
                    statusSpan.style.color = "";
                }, 3000);
                
            } catch (e) {
                console.error(e);
                statusSpan.textContent = "Error!";
                statusSpan.style.color = "var(--accent-error)";
                alert("Audio upload failed: " + e.message);
                setTimeout(() => {
                    statusSpan.textContent = originalText;
                    statusSpan.style.color = "";
                }, 4000);
            } finally {
                fileInput.value = ""; // clear input
            }
        }

        window.uploadCustomMusic = uploadCustomMusic;

        // Fetch scanned folder metadata
        async function loadBrowserFolders() {
            try {
                let cont = document.getElementById("browser-folders-container");
                if (!cont) return;
                let res = await fetch("/api/media/list");
                let data = await res.json();
                cont.innerHTML = "";
                
                // Add categories
                for (let category in data.folders) {
                    let subdirs = data.folders[category];
                    
                    if (Array.isArray(subdirs) && subdirs.length > 0) {
                        subdirs.forEach(sub => {
                            let folderPath = "";
                            if (category === "characters") {
                                folderPath = `pinterest/characters/${sub}`;
                            } else if (category === "pinterest") {
                                folderPath = `pinterest/${sub}`;
                            } else {
                                folderPath = `${category}/${sub}`;
                            }
                            
                            let card = document.createElement("div");
                            card.className = "folder-card";
                            card.setAttribute("onclick", `openFolder('${folderPath}')`);
                            card.innerHTML = `
                                <div class="folder-icon"><i data-lucide="folder"></i></div>
                                <div class="folder-name">${category}/${sub}</div>
                                <div class="folder-meta">Custom folder</div>
                            `;
                            cont.appendChild(card);
                        });
                    } else {
                        let folderPath = category;
                        let card = document.createElement("div");
                        card.className = "folder-card";
                        card.setAttribute("onclick", `openFolder('${folderPath}')`);
                        card.innerHTML = `
                            <div class="folder-icon"><i data-lucide="folder"></i></div>
                            <div class="folder-name">${category}</div>
                            <div class="folder-meta">Niche stock</div>
                        `;
                        cont.appendChild(card);
                    }
                }
                lucide.createIcons();
            } catch (e) {
                console.error("Failed to load browser folders", e);
            }
        }

        // Handle script niche change to automatically sync language selection
        function onScriptNicheChanged() {
            let niche = document.getElementById("script-niche").value;
            let langSel = document.getElementById("script-lang");
            if (langSel) {
                if (niche === "swahili" || niche.startsWith("swahili")) {
                    langSel.value = "swahili";
                } else {
                    langSel.value = "english";
                }
                updateVoiceOptions();
            }
        }
        window.onScriptNicheChanged = onScriptNicheChanged;

        function populateVoiceSelect(selectEl, lang) {
            let savedVal = selectEl.value;
            selectEl.innerHTML = "";
            if (currentConfig.voices && currentConfig.voices[lang]) {
                currentConfig.voices[lang].forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v;
                    
                    let label = v;
                    if (v.startsWith("puter:")) {
                        const parts = v.split(":");
                        const sp = parts[1] || "";
                        const vc = parts[2] || "";
                        label = `[PUTER ${sp.toUpperCase()}] ${vc.charAt(0).toUpperCase() + vc.slice(1)}`;
                    } else if (v.startsWith("direct-gemini:")) {
                        label = `[GEMINI] ` + v.split(":").pop();
                    } else if (v.includes("(")) {
                        label = v.split(" (")[0];
                    } else if (v.includes("-")) {
                        const parts = v.split("-");
                        if (parts.length >= 3) {
                            label = parts[2].replace("Neural", "");
                        }
                    }
                    opt.textContent = label;
                    if (savedVal && currentConfig.voices[lang].includes(savedVal)) {
                        if (v === savedVal) opt.selected = true;
                    } else if (v === currentConfig.default_voice) {
                        opt.selected = true;
                    }
                    selectEl.appendChild(opt);
                });
            }
        }

        // Dynamic voice update based on language selected
        function updateVoiceOptions() {
            let langSel = document.getElementById("script-lang");
            let bulkLangSel = document.getElementById("bulk-lang");
            
            if (langSel) {
                let lang = langSel.value;
                let voiceSel = document.getElementById("script-voice");
                if (voiceSel) populateVoiceSelect(voiceSel, lang);
            }
            
            if (bulkLangSel) {
                let lang = bulkLangSel.value;
                let voiceSel = document.getElementById("bulk-voice");
                if (voiceSel) populateVoiceSelect(voiceSel, lang);
            }
        }
        window.updateVoiceOptions = updateVoiceOptions;

        // Switch Tab UI
        function switchTab(tabId) {
            document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
            document.querySelectorAll(".tab-section").forEach(sec => sec.classList.remove("active"));
            
            // Find active nav item based on onclick attribute
            const activeNav = Array.from(document.querySelectorAll(".nav-item")).find(item => 
                item.getAttribute("onclick") && item.getAttribute("onclick").includes(`'${tabId}'`)
            );
            if (activeNav) activeNav.classList.add("active");
            
            if (tabId === 'scheduler') {
                loadUploadQueueList();
                setQueueVideoMode('rendered');
            } else if (tabId === 'creator' || tabId === 'bulk') {
                loadConfig().then(() => updateVoiceOptions());
            } else if (tabId === 'trends') {
                loadTrends(false);
            } else if (tabId === 'settings') {
                loadSettings();
            } else if (tabId === 'tts' || tabId === 'vlab') {
                initExplorerTTS();
            } else if (tabId === 'clipper') {
                loadClipperSources();
            }
            
            const targetTab = document.getElementById(`tab-${tabId}`);
            if (targetTab) targetTab.classList.add("active");
            
            const titleEl = document.getElementById("tab-title");
            if (titleEl) {
                titleEl.textContent = {
                    'creator': 'Script Creator',
                    'bulk': 'Bulk Generator',
                    'downloader': 'Downloader Hub',
                    'composer': 'Composer Timeline',
                    'lyrics-mode': 'Song to Reel Studio',
                    'clipper': 'Longform Clipper',
                    'publisher': 'Publisher Pipeline',
                    'scheduler': 'Scheduler Queue',
                    'trends': 'Trending Finder',
                    'tts': 'TTS Voice Explorer',
                    'vlab': 'Voice Lab (TTS Studio)',
                    'settings': 'Settings Control'
                }[tabId] || 'VideoFactory';
            }
        }

        // Generate AI Script
        async function generateAIScript() {
            let niche = document.getElementById("script-niche").value;
            let lang = document.getElementById("script-lang").value;
            let voice = document.getElementById("script-voice").value;
            let topic = document.getElementById("script-topic").value;
            let viral = document.getElementById("script-viral").checked;
            
            let btn = document.querySelector("#tab-creator .btn");
            btn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Generating...';
            btn.disabled = true;
            
            let script = null;
            
            // 1. Try Puter SDK Gemini 2.5 Flash first (fast, natural, high quality)
            if (typeof puter !== 'undefined' && puter.ai && typeof puter.ai.chat === 'function') {
                try {
                    const prompt = `You are a professional vertical reel / TikTok scriptwriter. Write an emotional, high-retention script in ${lang === 'swahili' ? 'natural Swahili (Kiswahili fasaha, chenye kugusa hisia, siyo cha kitabu)' : 'engaging English'} for niche: "${niche}"${topic ? ' about: ' + topic : ''}.${viral ? ' Use a curiosity-inducing viral hook.' : ''}
Return ONLY a valid raw JSON object (no markdown, no backticks, no extra text) with this format:
{
  "hook": "1 short opening sentence that grabs attention immediately",
  "body": [
    "Short impactful sentence 1",
    "Short emotional sentence 2",
    "Short powerful sentence 3"
  ],
  "cta": "1 short closing sentence or call to action"
}`;
                    const puterRes = await puter.ai.chat(prompt, { model: "gemini-2.5-flash" });
                    let text = puterRes?.message?.content || puterRes?.text || (typeof puterRes === 'string' ? puterRes : JSON.stringify(puterRes));
                    if (typeof text === 'string') {
                        text = text.replace(/```json/gi, '').replace(/```/g, '').trim();
                        const match = text.match(/\{[\s\S]*\}/);
                        if (match) text = match[0];
                        script = JSON.parse(text);
                    }
                } catch(pe) {
                    console.warn("Puter Gemini chat fallback to server:", pe);
                }
            }

            // 2. Server fallback if Puter wasn't available or errored
            if (!script) {
                try {
                    let res = await fetch("/api/script/generate", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({niche, language: lang, topic, viral})
                    });
                    script = await res.json();
                } catch(e) {
                    alert("Failed to generate script: " + e.message);
                }
            }
            
            if (script) {
                currentScript = script;
                displayScript(script);
            }
            
            btn.innerHTML = '<i data-lucide="sparkles"></i> Generate Script';
            btn.disabled = false;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }

        async function autoOrganizeExternalScript() {
            const rawInput = document.getElementById("raw-pasted-script").value;
            if (!rawInput || !rawInput.trim()) {
                alert("Please paste your script text into the box first!");
                return null;
            }

            const lang = document.getElementById("script-lang").value || "swahili";
            const niche = document.getElementById("script-niche").value || "gospel";

            let data = null;

            // 1. Try Puter SDK Gemini
            if (typeof puter !== 'undefined' && puter.ai && typeof puter.ai.chat === 'function') {
                try {
                    const prompt = `Convert the following raw text into a clean vertical reel script in ${lang}:
"${rawInput}"
Return ONLY valid JSON (no markdown, no backticks):
{
  "hook": "1 short punchy opening sentence",
  "body": ["sentence 1", "sentence 2", "sentence 3", "sentence 4"],
  "cta": "1 short call to action sentence"
}`;
                    const puterRes = await puter.ai.chat(prompt, { model: "gemini-2.5-flash" });
                    let text = puterRes?.message?.content || puterRes?.text || (typeof puterRes === 'string' ? puterRes : JSON.stringify(puterRes));
                    if (typeof text === 'string') {
                        text = text.replace(/```json/gi, '').replace(/```/g, '').trim();
                        const match = text.match(/\{[\s\S]*\}/);
                        if (match) text = match[0];
                        data = JSON.parse(text);
                    }
                } catch(pe) {
                    console.warn("Puter Gemini organize fallback to server:", pe);
                }
            }

            // 2. Server fallback
            if (!data) {
                try {
                    const res = await fetch("/api/script/organize_external", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            raw_text: rawInput,
                            language: lang,
                            niche: niche
                        })
                    });

                    if (!res.ok) {
                        const err = await res.json();
                        throw new Error(err.detail || "Failed to organize script");
                    }

                    data = await res.json();
                } catch(e) {
                    alert("Organize Script Error: " + e.message);
                    return null;
                }
            }

            if (data) {
                currentScript = data;
                displayScript(data);
                if (typeof lucide !== 'undefined') lucide.createIcons();
                alert("Script cleaned & formatted! Review lines below or send to Composer.");
                return data;
            }
            return null;
        }
        window.autoOrganizeExternalScript = autoOrganizeExternalScript;

        async function autoOrganizeAndSendToComposer() {
            const organized = await autoOrganizeExternalScript();
            if (organized) {
                goToComposer();
            }
        }
        window.autoOrganizeAndSendToComposer = autoOrganizeAndSendToComposer;

        // display script in editor cards
        function displayScript(script) {
            document.getElementById("editor-card").style.display = "block";
            document.getElementById("script-title-val").value = script.title || "Untitled Reel";
            document.getElementById("script-hook-val").value = script.hook || "";
            document.getElementById("script-cta-val").value = script.cta || "";
            
            let container = document.getElementById("script-lines-container");
            container.innerHTML = "";
            
            let body = script.body || [];
            body.forEach((line, idx) => {
                let card = document.createElement("div");
                card.className = "script-line-card";
                card.innerHTML = `
                    <div class="line-badge">${idx + 1}</div>
                    <input type="text" class="line-input script-body-line" value="${line}">
                    <button class="btn btn-secondary btn-circle" onclick="previewLineCard(this)">
                        <i data-lucide="play" style="width: 18px; height: 18px;"></i>
                    </button>
                `;
                container.appendChild(card);
            });
            lucide.createIcons();
            
            // Auto scroll down to editor
            document.getElementById("editor-card").scrollIntoView({ behavior: 'smooth' });
        }

        // Preview single line audio in browser
        async function previewLine(inputId) {
            let text = document.getElementById(inputId).value;
            let voice = document.getElementById("script-voice").value;
            await playPreview(text, voice);
        }

        async function previewLineCard(btn) {
            let text = btn.previousElementSibling.value;
            let voice = document.getElementById("script-voice").value;
            await playPreview(text, voice);
        }

        async function playPreview(text, voice) {
            if (!text) return;
            let player = document.getElementById("tts-audio-player");
            player.src = `/api/tts/preview?text=${encodeURIComponent(text)}&voice=${voice}`;
            player.play();
        }

        // Proceed to composer
        function goToComposer() {
            // Update current script with edited values
            if (currentScript) {
                currentScript.title = document.getElementById("script-title-val").value;
                currentScript.hook = document.getElementById("script-hook-val").value;
                currentScript.cta = document.getElementById("script-cta-val").value;
                
                let bodyLines = [];
                document.querySelectorAll(".script-body-line").forEach(inp => {
                    bodyLines.push(inp.value);
                });
                currentScript.body = bodyLines;
            }
            switchTab('composer');
        }

        // Update download options based on downloader chosen
        function updateDownloadOptions() {
            let engine = document.getElementById("dl-engine").value;
            if (engine === "pexels") {
                document.getElementById("dl-type-group").style.display = "flex";
                document.getElementById("dl-query-label").textContent = "Pexels Search Query";
                document.getElementById("dl-source").placeholder = "e.g. nature, waterfall, david bible...";
            } else {
                document.getElementById("dl-type-group").style.display = "none";
                document.getElementById("dl-query-label").textContent = "Pinterest Board URL or Niche Target";
                document.getElementById("dl-source").placeholder = "e.g. gospel, nature, or paste a board URL...";
            }
        }

        // Start background media downloader
        async function startDownload() {
            let engine = document.getElementById("dl-engine").value;
            let folder = document.getElementById("dl-folder").value;
            let mediaType = document.getElementById("dl-type").value;
            let source = document.getElementById("dl-source").value;
            let limit = document.getElementById("dl-limit").value;
            
            try {
                let res = await fetch("/api/download", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        engine,
                        folder,
                        media_type: mediaType,
                        source,
                        limit
                    })
                });
                if (res.ok) {
                    alert("Download started in the background! Check target folders shortly.");
                    loadBrowserFolders();
                } else {
                    alert("Failed to start download.");
                }
            } catch (e) {
                alert("Error connecting to server.");
            }
        }
        // --- BULK VIDEO CREATION SYSTEM ---
        let bulkRunning = false;
        let bulkVideos = [];
        let bulkBatchSize = 0;
        let bulkCurrentIndex = 0;
        let bulkPollingInterval = null;

        function toggleBulkInputs(disable) {
            document.getElementById("bulk-niche").disabled = disable;
            document.getElementById("bulk-lang").disabled = disable;
            document.getElementById("bulk-voice").disabled = disable;
            document.getElementById("bulk-topic").disabled = disable;
            document.getElementById("bulk-viral").disabled = disable;
            document.getElementById("bulk-music-only").disabled = disable;
            document.getElementById("bulk-batch-size").disabled = disable;
            document.getElementById("bulk-mood").disabled = disable;
            document.getElementById("bulk-music").disabled = disable;
            
            let genBtn = document.querySelector("#tab-bulk button");
            if (disable) {
                genBtn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Running Factory...';
                genBtn.disabled = true;
            } else {
                genBtn.innerHTML = '<i data-lucide="cpu"></i> LAUNCH BULK VIDEO FACTORY';
                genBtn.disabled = false;
            }
            lucide.createIcons();
        }

        async function startBulkVideoFactory() {
            if (bulkRunning) return;
            
            let niche = document.getElementById("bulk-niche").value;
            let lang = document.getElementById("bulk-lang").value;
            let voice = document.getElementById("bulk-voice").value;
            let topic = document.getElementById("bulk-topic").value;
            let viral = document.getElementById("bulk-viral").checked;
            let musicOnly = document.getElementById("bulk-music-only").checked;
            
            bulkBatchSize = parseInt(document.getElementById("bulk-batch-size").value);
            let mood = document.getElementById("bulk-mood").value;
            let music = document.getElementById("bulk-music").value;
            
            bulkRunning = true;
            bulkVideos = [];
            bulkCurrentIndex = 0;
            
            toggleBulkInputs(true);
            
            document.getElementById("bulk-factory-card").style.display = "block";
            document.getElementById("bulk-factory-card").scrollIntoView({ behavior: 'smooth' });
            document.getElementById("bulk-finished-gallery").style.display = "none";
            document.getElementById("bulk-gallery-container").innerHTML = "";
            document.getElementById("bulk-overall-status").textContent = `Progress: 0 of ${bulkBatchSize} Videos Compiled`;
            document.getElementById("bulk-overall-progress").style.width = "0%";
            document.getElementById("bulk-overall-percent").textContent = "0%";
            document.getElementById("bulk-active-console").textContent = "Initializing Bulk Video Factory...\n";
            
            let tasksCont = document.getElementById("bulk-tasks-container");
            tasksCont.innerHTML = "";
            for (let i = 0; i < bulkBatchSize; i++) {
                let taskCard = document.createElement("div");
                taskCard.id = `bulk-task-${i}`;
                taskCard.className = "script-line-card";
                taskCard.style.padding = "0.75rem 1rem";
                taskCard.style.background = "rgba(255,255,255,0.01)";
                taskCard.innerHTML = `
                    <div class="line-badge" style="width: 28px; height: 28px; font-size: 0.75rem;">${i+1}</div>
                    <div style="flex-grow: 1; display: flex; flex-direction: column; gap: 0.2rem; min-width: 0;">
                        <span id="bulk-task-title-${i}" style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Video ${i+1}: Waiting...</span>
                        <span id="bulk-task-status-${i}" style="font-size: 0.75rem; color: var(--text-muted);">Queued</span>
                    </div>
                    <div id="bulk-task-icon-${i}" style="flex-shrink: 0; color: var(--text-muted);">
                        <i data-lucide="clock" style="width: 16px; height: 16px;"></i>
                    </div>
                `;
                tasksCont.appendChild(taskCard);
            }
            lucide.createIcons();
            
            runNextBulkVideo(niche, lang, voice, topic, viral, mood, music, musicOnly);
        }

        async function runNextBulkVideo(niche, lang, voice, topic, viral, mood, music, musicOnly) {
            if (bulkCurrentIndex >= bulkBatchSize) {
                bulkRunning = false;
                toggleBulkInputs(false);
                document.getElementById("bulk-overall-status").textContent = `SUCCESS: Completed ${bulkBatchSize} of ${bulkBatchSize} Videos!`;
                document.getElementById("bulk-overall-progress").style.width = "100%";
                document.getElementById("bulk-overall-percent").textContent = "100%";
                document.getElementById("bulk-active-console").textContent += "\nAll bulk videos completed successfully!\n";
                
                let genBtn = document.querySelector("#tab-bulk button");
                genBtn.innerHTML = '<i data-lucide="cpu"></i> LAUNCH BULK VIDEO FACTORY';
                lucide.createIcons();
                
                alert(`Bulk Video Factory completed! Generated ${bulkBatchSize} videos successfully.`);
                return;
            }
            
            let idx = bulkCurrentIndex;
            let card = document.getElementById(`bulk-task-${idx}`);
            card.style.background = "rgba(168, 85, 247, 0.05)";
            card.style.borderColor = "rgba(168, 85, 247, 0.3)";
            
            let statusLabel = document.getElementById(`bulk-task-status-${idx}`);
            let titleLabel = document.getElementById(`bulk-task-title-${idx}`);
            let iconDiv = document.getElementById(`bulk-task-icon-${idx}`);
            
            let script = {};
            
            if (musicOnly) {
                statusLabel.textContent = "Setting up music-only mode...";
                statusLabel.style.color = "var(--primary)";
                iconDiv.innerHTML = '<i data-lucide="loader" class="animate-spin" style="color: var(--primary);"></i>';
                lucide.createIcons();
                titleLabel.textContent = `Video ${idx+1}: Instrumental Reel`;
                titleLabel.style.color = "var(--text-main)";
            } else {
                statusLabel.textContent = "Generating script...";
                statusLabel.style.color = "var(--primary)";
                iconDiv.innerHTML = '<i data-lucide="loader" class="animate-spin" style="color: var(--primary);"></i>';
                lucide.createIcons();
                
                document.getElementById("bulk-active-console").textContent += `\n--- Video ${idx+1}/${bulkBatchSize}: Generating Script ---\n`;
                
                try {
                    let res = await fetch("/api/script/generate", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({
                            niche,
                            language: lang,
                            topic: topic || null,
                            viral
                        })
                    });
                    
                    if (!res.ok) {
                        throw new Error("Script generation failed.");
                    }
                    
                    script = await res.json();
                    script.voice = voice;
                    
                    titleLabel.textContent = `Video ${idx+1}: ${script.title || "Untitled"}`;
                    titleLabel.style.color = "var(--text-main)";
                } catch (e) {
                    handleBulkVideoError(idx, e.message, niche, lang, voice, topic, viral, mood, music, musicOnly);
                    return;
                }
            }
            
            document.getElementById("bulk-active-console").textContent += `Compiling video...\n`;
            statusLabel.textContent = "Compiling (10%)...";
            statusLabel.style.color = "var(--accent-warning)";
            iconDiv.innerHTML = '<i data-lucide="sliders" class="animate-pulse" style="color: var(--accent-warning);"></i>';
            lucide.createIcons();
            
            try {
                let renderRes = await fetch("/api/render", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        script,
                        niche,
                        mood,
                        music_path: music || null,
                        music_only: musicOnly
                    })
                });
                
                if (!renderRes.ok) {
                    let err = await renderRes.json();
                    throw new Error("Render trigger failed: " + err.detail);
                }
                
                let checkProgress = async () => {
                    try {
                        let statusRes = await fetch("/api/render/status");
                        let statusData = await statusRes.json();
                        
                        document.getElementById("bulk-active-console").textContent = `--- Video ${idx+1}/${bulkBatchSize}: Compiling ---\n` + statusData.log;
                        let cons = document.getElementById("bulk-active-console");
                        cons.scrollTop = cons.scrollHeight;
                        
                        statusLabel.textContent = `Compiling (${statusData.progress}%)...`;
                        
                        if (statusData.status === "completed") {
                            clearInterval(bulkPollingInterval);
                            
                            statusLabel.textContent = "Completed!";
                            statusLabel.style.color = "var(--accent-success)";
                            iconDiv.innerHTML = '<i data-lucide="check-circle" style="color: var(--accent-success);"></i>';
                            card.style.background = "rgba(16, 185, 129, 0.03)";
                            card.style.borderColor = "rgba(16, 185, 129, 0.2)";
                            lucide.createIcons();
                            
                            addVideoToBulkGallery(statusData.output_file);
                            
                            bulkCurrentIndex++;
                            let overallPercent = Math.round((bulkCurrentIndex / bulkBatchSize) * 100);
                            document.getElementById("bulk-overall-status").textContent = `Progress: ${bulkCurrentIndex} of ${bulkBatchSize} Videos Compiled`;
                            document.getElementById("bulk-overall-progress").style.width = `${overallPercent}%`;
                            document.getElementById("bulk-overall-percent").textContent = `${overallPercent}%`;
                            
                            setTimeout(() => {
                                runNextBulkVideo(niche, lang, voice, topic, viral, mood, music, musicOnly);
                            }, 1500);
                            
                        } else if (statusData.status === "failed") {
                            clearInterval(bulkPollingInterval);
                            throw new Error("Subprocess reported render failure.");
                        }
                    } catch (pollErr) {
                        clearInterval(bulkPollingInterval);
                        handleBulkVideoError(idx, pollErr.message, niche, lang, voice, topic, viral, mood, music, musicOnly);
                    }
                };
                
                bulkPollingInterval = setInterval(checkProgress, 2000);
                
            } catch (err) {
                handleBulkVideoError(idx, err.message, niche, lang, voice, topic, viral, mood, music, musicOnly);
            }
        }

        function handleBulkVideoError(idx, errMsg, niche, lang, voice, topic, viral, mood, music, musicOnly) {
            let card = document.getElementById(`bulk-task-${idx}`);
            card.style.background = "rgba(239, 68, 68, 0.05)";
            card.style.borderColor = "rgba(239, 68, 68, 0.3)";
            
            let statusLabel = document.getElementById(`bulk-task-status-${idx}`);
            statusLabel.textContent = "Failed";
            statusLabel.style.color = "var(--accent-error)";
            
            let iconDiv = document.getElementById(`bulk-task-icon-${idx}`);
            iconDiv.innerHTML = '<i data-lucide="x-circle" style="color: var(--accent-error);"></i>';
            lucide.createIcons();
            
            document.getElementById("bulk-active-console").textContent += `\n❌ ERROR on Video ${idx+1}: ${errMsg}\n`;
            
            bulkCurrentIndex++;
            let overallPercent = Math.round((bulkCurrentIndex / bulkBatchSize) * 100);
            document.getElementById("bulk-overall-status").textContent = `Progress: ${bulkCurrentIndex} of ${bulkBatchSize} Videos Compiled`;
            document.getElementById("bulk-overall-progress").style.width = `${overallPercent}%`;
            document.getElementById("bulk-overall-percent").textContent = `${overallPercent}%`;
            
            setTimeout(() => {
                runNextBulkVideo(niche, lang, voice, topic, viral, mood, music, musicOnly);
            }, 2000);
        }

        function addVideoToBulkGallery(fileName) {
            let gallery = document.getElementById("bulk-finished-gallery");
            gallery.style.display = "block";
            
            let cont = document.getElementById("bulk-gallery-container");
            
            let card = document.createElement("div");
            card.className = "file-card";
            card.style.maxWidth = "260px";
            
            card.innerHTML = `
                <div class="file-preview-container" style="height: 180px;">
                    <video class="file-preview-video" loop muted autoplay playsinline>
                        <source src="/output/videos/${fileName}" type="video/mp4">
                    </video>
                </div>
                <div class="file-info" style="padding: 0.75rem;">
                    <div class="file-name" style="font-size: 0.8rem;" title="${fileName}">${fileName}</div>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <button class="btn btn-secondary" style="flex: 1; padding: 0.35rem 0.5rem; font-size: 0.75rem; gap: 0.2rem;" onclick="previewBulkVideo('${fileName}')">
                            <i data-lucide="eye" style="width: 12px; height: 12px;"></i> View
                        </button>
                        <a href="/output/videos/${fileName}" download class="btn" style="padding: 0.35rem 0.5rem; font-size: 0.75rem; gap: 0.2rem;">
                            <i data-lucide="download" style="width: 12px; height: 12px;"></i> Get
                        </a>
                    </div>
                </div>
            `;
            cont.appendChild(card);
            lucide.createIcons();
        }

        function previewBulkVideo(fileName) {
            switchTab('composer');
            let previewCard = document.getElementById("phone-preview-card");
            let player = document.getElementById("rendered-video-player");
            player.src = `/output/videos/${fileName}`;
            previewCard.style.display = "flex";
            player.play();
            previewCard.scrollIntoView({ behavior: 'smooth' });
        }

        // Trigger compilation/rendering
        async function startComposing() {
            let musicOnly = document.getElementById("render-music-only").checked;
            if (!musicOnly && !currentScript) {
                alert("Please generate or load a script first in the Script Creator tab!");
                switchTab('creator');
                return;
            }
            
            let mood = document.getElementById("render-mood").value;
            let music = document.getElementById("render-music").value;
            let niche = document.getElementById("script-niche").value;

            let aspectRatioEl = document.getElementById("render-aspect-ratio");
            let captionStyleEl = document.getElementById("render-caption-style");
            let transitionStyleEl = document.getElementById("render-transition-style");
            let pitchShiftEl = document.getElementById("render-voice-pitch");
            let eqPresetEl = document.getElementById("render-voice-eq");

            let aspectRatio = aspectRatioEl ? aspectRatioEl.value : "9:16";
            let captionStyle = captionStyleEl ? captionStyleEl.value : "typing";
            let transitionStyle = transitionStyleEl ? transitionStyleEl.value : "whip_zoom";
            let pitchShift = pitchShiftEl ? parseFloat(pitchShiftEl.value) : 1.5;
            let eqPreset = eqPresetEl ? eqPresetEl.value : "warm_studio";
            
            try {
                let res = await fetch("/api/render", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        script: musicOnly ? {} : currentScript,
                        niche,
                        mood,
                        music_path: music || null,
                        music_only: musicOnly,
                        aspect_ratio: aspectRatio,
                        caption_style: captionStyle,
                        transition_style: transitionStyle,
                        pitch_shift: pitchShift,
                        eq_preset: eqPreset
                    })
                });
                
                if (res.ok) {
                    document.getElementById("render-status-txt").textContent = "RENDERING";
                    document.getElementById("render-step-label").textContent = "🚀 Starting render worker...";
                    document.getElementById("render-progress").style.width = "5%";
                    document.getElementById("render-pct-label").textContent = "5%";
                    document.getElementById("render-console").textContent = "Rendering started on server. Monitoring progress...\n";
                    document.getElementById("render-live-indicator").style.display = "flex";
                    document.querySelectorAll(".render-chip").forEach(c => c.classList.remove("active", "done"));
                    
                    const hudEl = document.getElementById("render-telemetry-hud");
                    if (hudEl) hudEl.style.display = "none";

                    if (pollingInterval) clearInterval(pollingInterval);
                    pollingInterval = setInterval(pollRenderProgress, 750);
                } else {
                    let err = await res.json();
                    alert("Render failed: " + err.detail);
                }
            } catch (e) {
                alert("Connection failed.");
            }
        }

        // Global store for latest completed output
        let currentRenderedOutputFile = "";

        // Poll rendering logs and status with high-frequency telemetry
        async function pollRenderProgress() {
            try {
                let res = await fetch("/api/render/status");
                let data = await res.json();
                
                const pct = data.progress || 0;

                // ── Status badge ──
                document.getElementById("render-status-txt").textContent = data.status.toUpperCase();

                // ── Smooth progress bar fill ──
                document.getElementById("render-progress").style.width = `${pct}%`;

                // ── Percentage counter ──
                document.getElementById("render-pct-label").textContent = `${pct}%`;

                // ── Step label ──
                const stepLabel = data.step_label || "";
                if (stepLabel) {
                    document.getElementById("render-step-label").textContent = stepLabel;
                }

                // ── Live pulse indicator ──
                const liveEl = document.getElementById("render-live-indicator");
                if (data.status === "rendering") {
                    liveEl.style.display = "flex";
                } else {
                    liveEl.style.display = "none";
                }

                // ── Telemetry HUD: Frame, FPS, ETA ──
                const hudEl = document.getElementById("render-telemetry-hud");
                if (hudEl) {
                    if (data.status === "rendering" && (data.current_frame || data.fps || data.eta)) {
                        hudEl.style.display = "flex";
                        const frameVal = document.getElementById("hud-frame-val");
                        if (frameVal && data.current_frame && data.total_frames) {
                            frameVal.textContent = `${data.current_frame}/${data.total_frames}`;
                        }
                        const fpsVal = document.getElementById("hud-fps-val");
                        if (fpsVal && data.fps) {
                            fpsVal.textContent = `${data.fps.toFixed(1)} fps`;
                        }
                        const etaVal = document.getElementById("hud-eta-val");
                        if (etaVal && data.eta) {
                            etaVal.textContent = data.eta;
                        }
                    } else if (data.status !== "rendering") {
                        hudEl.style.display = "none";
                    }
                }

                // ── Step chips: mark active/done by progress range ──
                document.querySelectorAll(".render-chip").forEach(chip => {
                    const chipMin = parseInt(chip.dataset.min);
                    const chipMax = parseInt(chip.dataset.max);
                    chip.classList.remove("active", "done");
                    if (pct >= chipMin && pct <= chipMax) {
                        chip.classList.add("active");
                    } else if (pct > chipMax) {
                        chip.classList.add("done");
                    }
                });

                // ── Console log ──
                document.getElementById("render-console").textContent = data.log;
                let cons = document.getElementById("render-console");
                cons.scrollTop = cons.scrollHeight;
                
                if (data.status === "completed" || data.status === "failed") {
                    clearInterval(pollingInterval);
                    if (data.status === "completed") {
                        currentRenderedOutputFile = data.output_file || "";
                        // Show the phone preview card with smooth transition
                        let card = document.getElementById("phone-preview-card");
                        let player = document.getElementById("rendered-video-player");
                        if (player && data.output_file) {
                            player.src = `/output/videos/${data.output_file}`;
                            card.style.display = "flex";
                            card.scrollIntoView({ behavior: "smooth", block: "nearest" });
                            setTimeout(() => {
                                player.play().catch(() => {});
                            }, 300);
                        }
                        if (window.lucide) lucide.createIcons();
                    } else {
                        document.getElementById("render-step-label").textContent = "❌ Render failed — check console for details";
                    }
                }
            } catch (e) {
                console.error("Polling failed", e);
            }
        }

        // Music player preview toggle
        let musicPlaying = false;
        
        function onMusicSelected() {
            stopMusicPreview();
        }
        
        function stopMusicPreview() {
            let player = document.getElementById("bg-music-player");
            player.pause();
            musicPlaying = false;
            let btn = document.getElementById("music-preview-btn");
            if (btn) {
                btn.innerHTML = '<i data-lucide="play" style="width: 18px; height: 18px;"></i>';
            }
            lucide.createIcons();
        }
        
        function toggleMusicPreview() {
            let select = document.getElementById("render-music");
            let selectedOption = select.options[select.selectedIndex];
            let url = selectedOption.getAttribute("data-url");
            
            if (!url) {
                alert("Please select a background music track to preview.");
                return;
            }
            
            let player = document.getElementById("bg-music-player");
            let btn = document.getElementById("music-preview-btn");
            
            if (musicPlaying) {
                player.pause();
                musicPlaying = false;
                btn.innerHTML = '<i data-lucide="play" style="width: 18px; height: 18px;"></i>';
            } else {
                player.src = url;
                player.play();
                musicPlaying = true;
                btn.innerHTML = '<i data-lucide="pause" style="width: 18px; height: 18px;"></i>';
            }
            lucide.createIcons();
        }

        // Download rendered video directly
        function downloadRenderedVideo() {
            let player = document.getElementById("rendered-video-player");
            let targetSrc = (player && player.src) ? player.src : (currentRenderedOutputFile ? `/output/videos/${currentRenderedOutputFile}` : "");
            if (targetSrc) {
                let a = document.createElement("a");
                a.href = targetSrc;
                a.download = targetSrc.split('/').pop() || "reel.mp4";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } else {
                alert("No rendered video available yet.");
            }
        }

        // Copy rendered video path to clipboard
        function copyRenderedVideoPath() {
            let fileName = currentRenderedOutputFile;
            if (!fileName) {
                let player = document.getElementById("rendered-video-player");
                if (player && player.src) {
                    fileName = player.src.split('/').pop();
                }
            }
            if (!fileName) {
                alert("No rendered video available to copy.");
                return;
            }
            const relativePath = `output/videos/${fileName}`;
            navigator.clipboard.writeText(relativePath).then(() => {
                alert(`Copied output path: ${relativePath}`);
            }).catch(() => {
                prompt("Copy video path:", relativePath);
            });
        }

        // Open fullscreen video player
        function openFullscreenPreview() {
            let player = document.getElementById("rendered-video-player");
            if (player) {
                if (player.requestFullscreen) {
                    player.requestFullscreen();
                } else if (player.webkitRequestFullscreen) {
                    player.webkitRequestFullscreen();
                }
            }
        }

        // Open specific asset folder
        async function openFolder(folderPath) {
            try {
                let res = await fetch(`/api/media/files?folder=${encodeURIComponent(folderPath)}`);
                let data = await res.json();
                
                document.getElementById("browser-folder-title").textContent = `Folder: ${folderPath}`;
                document.getElementById("browser-file-count").textContent = `${data.files.length} file(s) found`;
                
                let container = document.getElementById("browser-files-container");
                container.innerHTML = "";
                
                if (data.files.length === 0) {
                    container.innerHTML = `
                        <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 4rem 1rem;">
                            <i data-lucide="image-off" style="width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.5;"></i>
                            <p>No media files found in this folder.</p>
                            <p style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.6;">Use the Downloader Hub to download assets into this folder.</p>
                        </div>
                    `;
                } else {
                    data.files.forEach(file => {
                        let card = document.createElement("div");
                        card.className = "file-card";
                        
                        let previewHTML = "";
                        if (file.type === "image") {
                            previewHTML = `<img src="${file.url}" class="file-preview-img" alt="${file.name}">`;
                        } else if (file.type === "video") {
                            previewHTML = `
                                <video class="file-preview-video" loop muted autoplay playsinline>
                                    <source src="${file.url}" type="video/mp4">
                                </video>
                            `;
                        }
                        
                        card.innerHTML = `
                            <div class="file-preview-container">
                                ${previewHTML}
                            </div>
                            <div class="file-info">
                                <div class="file-name" title="${file.name}">${file.name}</div>
                                <div class="file-type-badge">${file.type}</div>
                            </div>
                        `;
                        container.appendChild(card);
                    });
                }
                
                // Toggle view
                document.getElementById("browser-folders-view").style.display = "none";
                document.getElementById("browser-files-view").style.display = "block";
                lucide.createIcons();
            } catch (e) {
                alert("Failed to load folder contents.");
                console.error(e);
            }
        }

        // Go back to folders view
        function backToFolders() {
            document.getElementById("browser-files-view").style.display = "none";
            document.getElementById("browser-folders-view").style.display = "block";
        }

        // Load templates dynamically
        async function loadTemplateScripts() {
            try {
                let res = await fetch("/api/scripts/list");
                let data = await res.json();
                if (data.scripts.length > 0) {
                    // Pick a random template to show
                    let randomScript = data.scripts[Math.floor(Math.random() * data.scripts.length)];
                    currentScript = randomScript;
                    currentScript.voice = document.getElementById("script-voice").value;
                    displayScript(currentScript);
                } else {
                    alert("No local template scripts found.");
                }
            } catch (e) {
                alert("Failed to load local templates.");
            }
        }

        // --- PIPELINE PUBLISHER LOGIC ---

        async function loadPipelineConfig() {
            try {
                let res = await fetch("/api/pipeline/config");
                let data = await res.json();
                
                // Update active platforms badges
                updatePlatformUI("youtube", data.active_platforms.includes("youtube"), data.youtube_ready);
                updatePlatformUI("tiktok", data.active_platforms.includes("tiktok"), data.tiktok_ready);
                updatePlatformUI("instagram", data.active_platforms.includes("instagram"), data.instagram_ready);
                
            } catch (e) {
                console.error("Failed to load pipeline config", e);
            }
        }

        function updatePlatformUI(platformId, isActive, isReady) {
            let el = document.getElementById(`plat-${platformId}`);
            let textEl = el.querySelector("span");
            let iconName = platformId === "youtube" ? "youtube" : (platformId === "tiktok" ? "music-2" : "instagram");
            
            el.className = "platform-badge";
            
            if (!isActive) {
                el.classList.add("inactive");
                textEl.textContent = `${platformId.charAt(0).toUpperCase() + platformId.slice(1)}: Disabled`;
            } else if (isReady) {
                el.classList.add("active");
                textEl.textContent = `${platformId.charAt(0).toUpperCase() + platformId.slice(1)}: Connected (Profile OK)`;
            } else {
                el.classList.add("warning");
                textEl.textContent = `${platformId.charAt(0).toUpperCase() + platformId.slice(1)}: Sign-In Required (Interactive mode)`;
            }
        }

        async function loadPipelineLogs() {
            try {
                let res = await fetch("/api/pipeline/log");
                let data = await res.json();
                let tbody = document.getElementById("pub-history-body");
                tbody.innerHTML = "";
                
                let keys = Object.keys(data.log).sort().reverse();
                if (keys.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 2rem;">No videos published yet.</td>
                        </tr>
                    `;
                    return;
                }
                
                keys.forEach(k => {
                    let logItem = data.log[k];
                    let tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td style="font-weight: 700; color: #a855f7;">${k}</td>
                        <td style="font-family: var(--font-code); font-size: 0.85rem;">${logItem.video}</td>
                        <td>
                            ${logItem.platforms.map(p => `<span style="font-size: 0.75rem; font-weight: 700; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; padding: 0.15rem 0.5rem; border-radius: 4px; margin-right: 0.25rem;">${p.toUpperCase()}</span>`).join("")}
                        </td>
                        <td style="color: var(--text-muted);">${logItem.timestamp}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                console.error("Failed to load logs", e);
            }
        }

        async function startPipeline() {
            let force = document.getElementById("pipeline-force").checked;
            
            try {
                let res = await fetch("/api/pipeline/run", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ force })
                });
                
                if (res.ok) {
                    document.getElementById("pipeline-status-txt").textContent = "Status: Executing daily run...";
                    document.getElementById("pipeline-progress").style.width = "5%";
                    document.getElementById("pipeline-console").textContent = "Pipeline run started on backend. Monitoring status...\n";
                    
                    if (pipelineInterval) clearInterval(pipelineInterval);
                    pipelineInterval = setInterval(pollPipelineProgress, 2500);
                } else {
                    let err = await res.json();
                    alert("Pipeline trigger failed: " + err.detail);
                }
            } catch (e) {
                alert("Server connection failed.");
            }
        }

        async function pollPipelineProgress() {
            try {
                let res = await fetch("/api/pipeline/status");
                let data = await res.json();
                
                document.getElementById("pipeline-status-txt").textContent = `Status: ${data.status.toUpperCase()}`;
                document.getElementById("pipeline-progress").style.width = `${data.progress}%`;
                document.getElementById("pipeline-console").textContent = data.log;
                
                let cons = document.getElementById("pipeline-console");
                cons.scrollTop = cons.scrollHeight;
                
                if (data.status === "completed" || data.status === "failed") {
                    clearInterval(pipelineInterval);
                    if (data.status === "completed") {
                        alert("Daily Pipeline finished successfully!");
                    } else {
                        alert("Daily Pipeline failed. Check console for details.");
                    }
                    await loadPipelineLogs();
                    await loadPipelineConfig();
                }
            } catch (e) {
                console.error("Pipeline polling failed", e);
            }
        }

        async function checkLoginSession(platform) {
            try {
                let res = await fetch(`/api/publisher/check-session?platform=${platform}`);
                let data = await res.json();
                alert(data.message);
            } catch (e) {
                alert("Failed to trigger session check.");
            }
        }

        // ============================================================
        // SCHEDULED VIDEO QUEUE FRONTEND LOGIC
        // ============================================================
        let queueVideoMode = "rendered"; // "rendered" or "local"

        function setQueueVideoMode(mode) {
            queueVideoMode = mode;
            let btnRendered = document.getElementById("btn-mode-rendered");
            let btnLocal = document.getElementById("btn-mode-local");
            let groupRendered = document.getElementById("group-video-rendered");
            let groupLocal = document.getElementById("group-video-local");
            
            // Reset preview player
            document.getElementById("group-video-preview").style.display = "none";
            let player = document.getElementById("queue-video-preview-player");
            player.src = "";
            player.load();
            
            if (mode === "rendered") {
                btnRendered.className = "btn";
                btnLocal.className = "btn btn-secondary";
                groupRendered.style.display = "flex";
                groupLocal.style.display = "none";
                loadRenderedVideoList();
            } else {
                btnRendered.className = "btn btn-secondary";
                btnLocal.className = "btn";
                groupRendered.style.display = "none";
                groupLocal.style.display = "flex";
            }
        }

        async function loadRenderedVideoList() {
            try {
                let res = await fetch("/api/videos/rendered");
                let data = await res.json();
                let select = document.getElementById("queue-rendered-video");
                select.innerHTML = '<option value="">-- Select a Video --</option>';
                
                data.videos.forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v.name;
                    opt.setAttribute("data-size", v.size_mb);
                    opt.setAttribute("data-date", v.created_at);
                    opt.textContent = `${v.name} (${v.size_mb} MB) - ${v.created_at}`;
                    select.appendChild(opt);
                });
                
                onRenderedVideoSelected();
            } catch (e) {
                console.error("Failed to load rendered videos", e);
            }
        }

        function onRenderedVideoSelected() {
            let select = document.getElementById("queue-rendered-video");
            let infoSpan = document.getElementById("rendered-video-info");
            let titleInput = document.getElementById("queue-title");
            let previewGroup = document.getElementById("group-video-preview");
            let player = document.getElementById("queue-video-preview-player");
            
            if (select.selectedIndex <= 0) {
                infoSpan.textContent = "";
                previewGroup.style.display = "none";
                player.src = "";
                player.load();
                return;
            }
            
            let selectedOption = select.options[select.selectedIndex];
            let size = selectedOption.getAttribute("data-size");
            let date = selectedOption.getAttribute("data-date");
            
            infoSpan.innerHTML = `<strong>Selected:</strong> Size: ${size} MB | Compiled: ${date}`;
            
            // Set preview source and show player
            player.src = `/output/videos/${selectedOption.value}`;
            previewGroup.style.display = "flex";
            player.play();
            
            if (!titleInput.value) {
                let name = selectedOption.value.replace(/\.[^/.]+$/, "");
                let formatted = name.replace(/[_-]/g, " ").replace(/\b\w/g, c => c.toUpperCase());
                titleInput.value = formatted;
            }
        }

        function setQueueTimePreset(preset) {
            let now = new Date();
            let year = now.getFullYear();
            let month = String(now.getMonth() + 1).padStart(2, '0');
            let day = String(now.getDate()).padStart(2, '0');
            
            let targetHour = 8;
            let targetMin = 0;
            
            if (preset === 'morning') {
                targetHour = 8; targetMin = 0;
            } else if (preset === 'noon') {
                targetHour = 12; targetMin = 30;
            } else if (preset === 'afternoon') {
                targetHour = 16; targetMin = 30;
            } else if (preset === 'evening') {
                targetHour = 20; targetMin = 0;
            }
            
            let targetDate = new Date(year, now.getMonth(), now.getDate(), targetHour, targetMin);
            if (now >= targetDate) {
                targetDate.setDate(targetDate.getDate() + 1);
            }
            
            let targetYear = targetDate.getFullYear();
            let targetMonth = String(targetDate.getMonth() + 1).padStart(2, '0');
            let targetDay = String(targetDate.getDate()).padStart(2, '0');
            let targetHourStr = String(targetDate.getHours()).padStart(2, '0');
            let targetMinStr = String(targetDate.getMinutes()).padStart(2, '0');
            
            let datetimeStr = `${targetYear}-${targetMonth}-${targetDay}T${targetHourStr}:${targetMinStr}`;
            document.getElementById("queue-datetime").value = datetimeStr;
        }

        function onQueueVideoSelected() {
            let fileInput = document.getElementById("queue-video-file");
            let label = document.getElementById("queue-video-label");
            let previewGroup = document.getElementById("group-video-preview");
            let player = document.getElementById("queue-video-preview-player");
            
            if (fileInput.files.length > 0) {
                label.textContent = "Selected: " + fileInput.files[0].name;
                
                // Generate a local object URL for previewing
                let url = URL.createObjectURL(fileInput.files[0]);
                player.src = url;
                previewGroup.style.display = "flex";
                player.play();
            } else {
                label.textContent = "Click or Drag to Select Video File";
                previewGroup.style.display = "none";
                player.src = "";
                player.load();
            }
        }

        function onQueueThumbSelected() {
            let fileInput = document.getElementById("queue-thumb-file");
            let label = document.getElementById("queue-thumb-label");
            if (fileInput.files.length > 0) {
                label.textContent = "Selected Thumbnail: " + fileInput.files[0].name;
            } else {
                label.textContent = "Select custom thumbnail image";
            }
        }

        async function perfectDescriptionAI() {
            let desc = document.getElementById("queue-description").value;
            let niche = document.getElementById("queue-niche").value;
            let btn = document.getElementById("queue-perfect-btn");
            
            if (!desc) {
                alert("Please type a draft description first!");
                return;
            }
            
            btn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Polishing...';
            btn.disabled = true;
            lucide.createIcons();
            
            try {
                let res = await fetch("/api/queue/perfect-description", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ description: desc, niche: niche })
                });
                
                if (res.ok) {
                    let data = await res.json();
                    document.getElementById("queue-description").value = data.perfected_description;
                } else {
                    alert("AI Polishing failed.");
                }
            } catch (e) {
                alert("Connection failed.");
            } finally {
                btn.innerHTML = '<i data-lucide="sparkles"></i> Perfect Description with AI';
                btn.disabled = false;
                lucide.createIcons();
            }
        }

        async function scheduleQueueVideo() {
            let videoInput = document.getElementById("queue-video-file");
            let thumbInput = document.getElementById("queue-thumb-file");
            let niche = document.getElementById("queue-niche").value;
            let title = document.getElementById("queue-title").value;
            let desc = document.getElementById("queue-description").value;
            let schedTime = document.getElementById("queue-datetime").value;
            
            let platforms = [];
            if (document.getElementById("queue-plat-youtube").checked) platforms.push("youtube");
            if (document.getElementById("queue-plat-tiktok").checked) platforms.push("tiktok");
            if (document.getElementById("queue-plat-instagram").checked) platforms.push("instagram");
            
            if (!schedTime) {
                alert("Please pick a scheduled date and time!");
                return;
            }
            if (platforms.length === 0) {
                alert("Please select at least one target platform!");
                return;
            }
            
            let scheduleBtn = document.querySelector("#tab-scheduler .btn");
            let origHtml = scheduleBtn.innerHTML;
            
            if (queueVideoMode === "rendered") {
                let renderedSelect = document.getElementById("queue-rendered-video");
                if (renderedSelect.selectedIndex <= 0) {
                    alert("Please select a rendered video from the list!");
                    return;
                }
                
                let videoName = renderedSelect.value;
                scheduleBtn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Scheduling copy...';
                scheduleBtn.disabled = true;
                lucide.createIcons();
                
                try {
                    let addRes = await fetch("/api/queue/add-rendered", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({
                            video_name: videoName,
                            title: title || videoName,
                            description: desc,
                            platforms: platforms,
                            scheduled_time: schedTime
                        })
                    });
                    
                    if (addRes.ok) {
                        alert("Rendered video scheduled successfully!");
                        document.getElementById("queue-title").value = "";
                        document.getElementById("queue-description").value = "";
                        document.getElementById("queue-datetime").value = "";
                        loadUploadQueueList();
                        loadRenderedVideoList();
                    } else {
                        let err = await addRes.json();
                        alert("Scheduling failed: " + err.detail);
                    }
                } catch (e) {
                    alert("Error during schedule: " + e.message);
                } finally {
                    scheduleBtn.innerHTML = origHtml;
                    scheduleBtn.disabled = false;
                    lucide.createIcons();
                }
                
            } else {
                if (videoInput.files.length === 0) {
                    alert("Please select a local video file first!");
                    return;
                }
                
                let formData = new FormData();
                formData.append("video", videoInput.files[0]);
                if (thumbInput.files.length > 0) {
                    formData.append("thumbnail", thumbInput.files[0]);
                }
                
                scheduleBtn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Uploading media assets...';
                scheduleBtn.disabled = true;
                lucide.createIcons();
                
                try {
                    let uploadRes = await fetch("/api/queue/upload", {
                        method: "POST",
                        body: formData
                    });
                    
                    if (!uploadRes.ok) {
                        throw new Error("File upload failed.");
                    }
                    
                    let uploadData = await uploadRes.json();
                    
                    let addRes = await fetch("/api/queue/add", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({
                            video_path: uploadData.video_path,
                            thumbnail_path: uploadData.thumbnail_path,
                            title: title || videoInput.files[0].name,
                            description: desc,
                            platforms: platforms,
                            scheduled_time: schedTime
                        })
                    });
                    
                    if (addRes.ok) {
                        alert("Video scheduled successfully!");
                        videoInput.value = "";
                        thumbInput.value = "";
                        document.getElementById("queue-title").value = "";
                        document.getElementById("queue-description").value = "";
                        document.getElementById("queue-datetime").value = "";
                        onQueueVideoSelected();
                        onQueueThumbSelected();
                        loadUploadQueueList();
                    } else {
                        alert("Scheduling failed.");
                    }
                } catch (e) {
                    alert("Error during schedule upload: " + e.message);
                } finally {
                    scheduleBtn.innerHTML = origHtml;
                    scheduleBtn.disabled = false;
                    lucide.createIcons();
                }
            }
        }

        async function loadUploadQueueList() {
            try {
                let res = await fetch("/api/queue/list");
                let data = await res.json();
                let cont = document.getElementById("queue-items-container");
                cont.innerHTML = "";
                
                if (!data.queue || data.queue.length === 0) {
                    cont.innerHTML = `
                        <div style="text-align: center; color: var(--text-muted); padding: 3rem 0;">
                            <i data-lucide="calendar-days" style="width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.5;"></i>
                            <p>No scheduled videos in queue.</p>
                        </div>
                    `;
                    lucide.createIcons();
                    return;
                }
                
                let sortedQueue = data.queue.sort((a,b) => new Date(a.scheduled_time) - new Date(b.scheduled_time));
                
                sortedQueue.forEach(item => {
                    let card = document.createElement("div");
                    card.className = "queue-card";
                    
                    let statusColor = "var(--text-muted)";
                    let statusLabel = item.status.toUpperCase();
                    if (item.status === "pending") statusColor = "var(--primary-glow)";
                    if (item.status === "publishing") statusColor = "var(--accent-warning)";
                    if (item.status === "published") statusColor = "var(--accent-success)";
                    if (item.status === "partial_success") statusColor = "var(--accent-warning)";
                    if (item.status === "failed") statusColor = "var(--accent-error)";
                    
                    let timeFormatted = item.scheduled_time ? new Date(item.scheduled_time).toLocaleString() : "Now";
                    let canPublishNow = ["pending", "failed"].includes(item.status);
                    let isPublishing = item.status === "publishing";
                    
                    card.innerHTML = `
                        <div class="queue-card-header">
                            <div style="display: flex; gap: 0.75rem; align-items: center; flex: 1; min-width: 0;">
                                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: ${statusColor}; box-shadow: 0 0 10px ${statusColor}; flex-shrink: 0;"></div>
                                <span style="font-weight: 700; font-size: 0.95rem; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.title}</span>
                                <span style="font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; background: ${statusColor}22; color: ${statusColor}; border: 1px solid ${statusColor}44; flex-shrink: 0;">${statusLabel}</span>
                            </div>
                            <div style="display: flex; gap: 0.5rem; align-items: center; flex-shrink: 0;">
                                ${canPublishNow ? `<button class="btn" onclick="publishNow('${item.id}')" style="padding: 0.4rem 0.75rem; font-size: 0.75rem; display: flex; align-items: center; gap: 0.3rem;" title="Upload Now">
                                    <i data-lucide="upload-cloud" style="width: 13px; height: 13px;"></i> Upload Now
                                </button>` : ''}
                                ${isPublishing ? `<span style="font-size: 0.75rem; color: var(--accent-warning); display: flex; align-items: center; gap: 0.3rem;"><i data-lucide="loader" class="animate-spin" style="width: 13px; height: 13px;"></i> Uploading...</span>` : ''}
                                <button class="btn btn-secondary btn-circle" onclick="deleteQueueItem('${item.id}')" style="background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.2); color: var(--accent-error);" title="Delete">
                                    <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                                </button>
                            </div>
                        </div>
                        <div class="queue-card-meta">
                            <div><strong>Scheduled:</strong> ${timeFormatted}</div>
                            <div><strong>Video File:</strong> ${item.video_path ? item.video_path.split(/[\\\/]/).pop() : 'N/A'}</div>
                            ${item.thumbnail_path ? `<div><strong>Thumbnail:</strong> ${item.thumbnail_path.split(/[\\\/]/).pop()}</div>` : ''}
                            <div style="margin-top: 0.5rem;">
                                <strong>Platforms:</strong> 
                                ${item.platforms.map(p => `<span style="font-size: 0.7rem; font-weight: 700; background: rgba(255,255,255,0.05); border: 1px solid var(--border-subtle); color: #fff; padding: 0.15rem 0.4rem; border-radius: 4px; margin-right: 0.25rem;">${p.toUpperCase()}</span>`).join("")}
                            </div>
                        </div>
                        ${item.publish_log ? `
                            <div style="background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 0.6rem; font-family: var(--font-code); font-size: 0.72rem; color: #a3e635; max-height: 100px; overflow-y: auto; white-space: pre-wrap; margin-top: 0.5rem; line-height: 1.4;">${item.publish_log}</div>
                        ` : ''}
                        ${item.error_message ? `
                            <div style="font-size: 0.75rem; color: var(--accent-error); font-weight: 600; margin-top: 0.5rem;">❌ Error: ${item.error_message}</div>
                        ` : ''}
                    `;
                    cont.appendChild(card);
                });
                lucide.createIcons();
            } catch (e) {
                console.error("Failed to load queue list", e);
            }
        }

        async function publishNow(itemId) {
            if (!confirm("Upload this video to YouTube NOW immediately?")) return;
            try {
                let res = await fetch(`/api/queue/publish-now/${itemId}`, { method: "POST" });
                let data = await res.json();
                if (res.ok) {
                    alert("✅ Upload triggered! Check the queue log for progress updates.");
                    loadUploadQueueList();
                } else {
                    alert("❌ Failed: " + (data.detail || "Unknown error"));
                }
            } catch (e) {
                alert("Connection error: " + e.message);
            }
        }

        async function deleteQueueItem(itemId) {
            if (!confirm("Are you sure you want to delete this scheduled post?")) return;
            try {
                let res = await fetch(`/api/queue/delete/${itemId}`, { method: "DELETE" });
                if (res.ok) {
                    loadUploadQueueList();
                } else {
                    alert("Delete failed.");
                }
            } catch (e) {
                alert("Connection failed.");
            }
        }

        // Setup periodic queue checker when tab is open
        setInterval(() => {
            let schedulerTab = document.getElementById("tab-scheduler");
            if (schedulerTab && schedulerTab.classList.contains("active")) {
                loadUploadQueueList();
            }
        }, 5000);

        // ============================================================
        // TRENDS FINDER FRONTEND LOGIC
        // ============================================================
        let allTrendsData = [];
        let activeTrendsCategory = 'all';

        const CHRISTIAN_CATEGORIES = [
            "church_news", "gospel_music", "gospel_artist", "christian_celeb", 
            "megachurch", "persecution", "revival", "bible_news", "african_church", "moral_issue", "prophecy"
        ];

        const SOURCE_EMOJIS = {
            'google_': '🌍', 'reddit/': '📱', 'hackernews': '💻',
            'bbc': '📺', 'aljazeera': '📡', 'dw_africa': '🌍',
            'christian_post': '✝️', 'charisma_news': '✝️', 'crosswalk': '✝️',
            'relevant_mag': '✝️', 'christianity_today': '✝️',
            'nation_ke': '🇰🇪', 'standardmedia_ke': '🇰🇪', 'thecitizen_tz': '🇹🇿',
            'youtube_trending': '▶️', 'wikipedia_events': '📖',
            'newsapi': '📰', 'guardian': '📰', 'gnews': '📰',
        };

        function getSourceEmoji(source) {
            for (const [key, emoji] of Object.entries(SOURCE_EMOJIS)) {
                if (source.startsWith(key) || source.includes(key)) return emoji;
            }
            return '🌐';
        }

        async function loadTrends(forceRefresh = false) {
            let container = document.getElementById("trends-container");
            
            // Build nice skeleton cards
            let skeletonHtml = '';
            for (let i = 0; i < 6; i++) {
                skeletonHtml += `
                    <div class="glass-card trend-card skeleton-loader" style="min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; padding: 1.25rem;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="width: 80px; height: 18px; background: rgba(255,255,255,0.08); border-radius: 4px;"></div>
                                <div style="width: 100px; height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px;"></div>
                            </div>
                            <div style="width: 90%; height: 20px; background: rgba(255,255,255,0.08); border-radius: 4px; margin-top: 1.5rem; margin-bottom: 0.5rem;"></div>
                            <div style="width: 70%; height: 20px; background: rgba(255,255,255,0.08); border-radius: 4px; margin-bottom: 0.5rem;"></div>
                            <div style="width: 50%; height: 12px; background: rgba(255,255,255,0.05); border-radius: 4px; margin-top: 1rem;"></div>
                        </div>
                        <div style="display: flex; gap: 0.75rem; align-items: center; margin-top: 1.5rem;">
                            <div style="flex-grow: 1; height: 36px; background: rgba(255,255,255,0.08); border-radius: 8px;"></div>
                            <div style="width: 36px; height: 36px; background: rgba(255,255,255,0.05); border-radius: 50%;"></div>
                        </div>
                    </div>
                `;
            }

            container.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 1.5rem 1rem; background: rgba(255,255,255,0.02); border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid var(--border-subtle); display: flex; align-items: center; justify-content: center; gap: 1rem;">
                    <i data-lucide="loader-2" style="width: 24px; height: 24px; animation: spin 1.5s linear infinite; color: var(--primary);"></i>
                    <span style="font-weight: 500;">
                        ${forceRefresh 
                            ? 'Scanning 15+ global sources in real-time (BBC, Al Jazeera, Wikipedia, YouTube, Reddit)...' 
                            : 'Loading cached trending topics from regional & faith boards...'}
                    </span>
                </div>
                ${skeletonHtml}
            `;
            lucide.createIcons();

            let refreshBtn = document.getElementById("trends-refresh-btn");
            if (refreshBtn) {
                let icon = refreshBtn.querySelector("i, svg, .lucide");
                if (icon) icon.classList.add("animate-spin");
            }

            try {
                let res = await fetch(`/api/trends/list?refresh=${forceRefresh}`);
                if (!res.ok) throw new Error("Failed to load trends");
                let data = await res.json();
                allTrendsData = data.trends || [];
                // Update cache info label
                let cacheInfo = document.getElementById('trends-cache-info');
                if (cacheInfo) {
                    let count = allTrendsData.length;
                    let timeStr = forceRefresh ? 'Just refreshed' : 'Cached';
                    cacheInfo.textContent = `${timeStr} · ${count} trends from 15+ sources`;
                }
                filterTrends();
            } catch (e) {
                container.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; color: var(--accent-error); padding: 3rem 1rem;">
                        <i data-lucide="alert-triangle" style="width: 48px; height: 48px; margin-bottom: 1rem;"></i>
                        <p>Error loading trending topics: ${e.message}</p>
                        <p style="font-size:0.82rem;margin-top:0.5rem;">Make sure the server is running and try refreshing.</p>
                    </div>
                `;
                lucide.createIcons();
            } finally {
                if (refreshBtn) {
                    let icon = refreshBtn.querySelector("i, svg, .lucide");
                    if (icon) icon.classList.remove("animate-spin");
                }
            }
        }

        function filterTrendsCategory(category) {
            activeTrendsCategory = category;
            
            // Toggle active filter style class
            let catContainer = document.getElementById("trends-categories");
            catContainer.querySelectorAll("button").forEach(btn => {
                btn.classList.remove("active-filter");
            });
            
            // Highlight clicked button
            const clickedBtn = Array.from(catContainer.querySelectorAll("button")).find(btn => 
                btn.getAttribute("onclick").includes(`'${category}'`)
            );
            if (clickedBtn) clickedBtn.classList.add("active-filter");
            
            filterTrends();
        }

        function filterTrends() {
            let query = document.getElementById("trends-search").value.toLowerCase();
            let filtered = allTrendsData;

            // Apply category filter
            if (activeTrendsCategory === 'christian') {
                filtered = filtered.filter(t => CHRISTIAN_CATEGORIES.includes(t.category));
            } else if (activeTrendsCategory === 'world') {
                filtered = filtered.filter(t => !CHRISTIAN_CATEGORIES.includes(t.category) && t.category !== 'general');
            } else if (activeTrendsCategory === 'east_africa') {
                filtered = filtered.filter(t =>
                    t.source.includes('kenya') || t.source.includes('tanzania') || t.source.includes('east_africa') ||
                    t.source.includes('nation_ke') || t.source.includes('standardmedia') || t.source.includes('thecitizen') ||
                    t.source.includes('reddit/Kenya') || t.source.includes('reddit/Tanzania') || t.source.includes('reddit/Uganda') || t.source.includes('reddit/Africa')
                );
            } else if (activeTrendsCategory === 'youtube') {
                filtered = filtered.filter(t => t.source.startsWith('youtube_trending'));
            } else if (activeTrendsCategory === 'reddit') {
                filtered = filtered.filter(t => t.source.startsWith('reddit'));
            } else if (['church_news','gospel_music','revival','persecution','megachurch','bible_news','african_church','moral_issue','prophecy','christian_celeb'].includes(activeTrendsCategory)) {
                filtered = filtered.filter(t => t.category === activeTrendsCategory);
            } else if (['tragedy','hope','victory','sports','tech','business','health','politics'].includes(activeTrendsCategory)) {
                filtered = filtered.filter(t => t.category === activeTrendsCategory);
            }

            // Apply search query
            if (query) {
                filtered = filtered.filter(t => 
                    t.title.toLowerCase().includes(query) || 
                    t.category.toLowerCase().includes(query) || 
                    t.source.toLowerCase().includes(query)
                );
            }

            renderTrends(filtered);
        }

        function renderTrends(trends) {
            let container = document.getElementById("trends-container");
            container.innerHTML = "";

            if (trends.length === 0) {
                container.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 4rem 1rem;">
                        <i data-lucide="search-code" style="width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.5;"></i>
                        <p>No matching trends found. Try broadening your filter or search query.</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            trends.forEach(trend => {
                let card = document.createElement("div");
                card.className = "glass-card trend-card";
                
                let isChristian = CHRISTIAN_CATEGORIES.includes(trend.category);
                let badgeClass = isChristian ? "trend-badge christian" : "trend-badge world";
                let badgeText = isChristian ? "Christian" : "World News";
                
                // Format category string nicely
                let displayCat = trend.category.replace(/_/g, " ");
                displayCat = displayCat.charAt(0).toUpperCase() + displayCat.slice(1);
                
                let emoji = getSourceEmoji(trend.source);
                let sourceClean = trend.source.replace(/_/g, " ").replace(/\//g, " r/");
                sourceClean = sourceClean.charAt(0).toUpperCase() + sourceClean.slice(1);
                
                card.innerHTML = `
                    <div>
                        <div class="trend-card-header">
                            <span class="${badgeClass}">${isChristian ? '✝️ ' + displayCat : badgeText}</span>
                            <span class="trend-source">${emoji} ${sourceClean}</span>
                        </div>
                        <h4 class="trend-title" style="margin-top: 1rem; margin-bottom: 0.5rem;" title="${trend.title}">${trend.title}</h4>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                            <span style="display:flex;align-items:center;gap:0.3rem;">
                                <i data-lucide="tag" style="width: 12px; height: 12px;"></i>
                                ${displayCat}
                            </span>
                            ${trend.score ? `<span style="display:flex;align-items:center;gap:0.3rem;"><i data-lucide="arrow-up" style="width: 12px; height: 12px;"></i>${trend.score.toLocaleString()} upvotes</span>` : ''}
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.75rem; align-items: center; margin-top: auto;">
                        <button class="btn" style="flex-grow: 1; padding: 0.6rem 1rem; font-size: 0.85rem;" onclick="spiritualizeTrend(${JSON.stringify(trend).replace(/"/g, '&quot;')})">
                            <i data-lucide="sparkles"></i>
                            Spiritualize
                        </button>
                        ${trend.url ? `
                            <a href="${trend.url}" target="_blank" class="btn btn-secondary btn-circle" title="View original article" style="display: inline-flex; width: 36px; height: 36px;">
                                <i data-lucide="external-link" style="width: 16px; height: 16px;"></i>
                            </a>
                        ` : ''}
                    </div>
                `;
                container.appendChild(card);
            });
            lucide.createIcons();
        }

        async function spiritualizeTrend(trend) {
            let overlay = document.getElementById("global-loading-overlay");
            let loadTxt = document.getElementById("global-loading-text");
            
            loadTxt.textContent = "Analyzing news and generating spiritualized script with AI...";
            overlay.style.display = "flex";
            
            // Get active default configurations from creator/settings tab
            let niche = document.getElementById("script-niche").value;
            let lang = document.getElementById("script-lang").value;
            let voice = document.getElementById("script-voice").value;

            try {
                let res = await fetch("/api/trends/generate-script", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        trend: trend,
                        niche: niche,
                        language: lang
                    })
                });
                
                if (!res.ok) throw new Error("API generation failed.");
                
                currentScript = await res.json();
                currentScript.voice = voice;
                
                // Show script in creator tab
                displayScript(currentScript);
                
                // Switch back to script editor
                switchTab('creator');
                
            } catch (e) {
                alert("Failed to turn trend into spiritual script: " + e.message);
            } finally {
                overlay.style.display = "none";
            }
        }

        // ============================================================
        // SETTINGS CONTROL FRONTEND LOGIC
        // ============================================================
        let voicesConfig = {};

        async function loadSettings() {
            let saveBtn = document.getElementById("settings-save-btn");
            let origHtml = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Loading Settings...';
            saveBtn.disabled = true;
            lucide.createIcons();

            try {
                // First read config to make sure we have active voice options
                let configRes = await fetch("/api/config");
                let configData = await configRes.json();
                voicesConfig = configData.voices || {};

                // Get settings
                let res = await fetch("/api/settings");
                let data = await res.json();
                
                // Set fields
                document.getElementById("settings-niche").value = data.NICHE;
                document.getElementById("settings-content-mode").value = data.CONTENT_MODE;
                document.getElementById("settings-lang").value = data.LANGUAGE;
                document.getElementById("settings-mode").value = data.MODE;
                
                // Set TTS provider
                document.getElementById("settings-tts-provider").value = data.TTS_PROVIDER || "edge-tts";
                
                // Populate voices list based on language
                updateSettingsVoiceDropdown(data.ACTIVE_VOICE);
                
                // TTS modifiers
                document.getElementById("settings-tts-rate").value = data.TTS_RATE;
                document.getElementById("settings-tts-pitch").value = data.TTS_PITCH;
                document.getElementById("settings-tts-volume").value = data.TTS_VOLUME;
                
                // Subtitles and audio (Default: Subtitles OFF, Audio Pure Passthrough)
                const subEnabledEl = document.getElementById("settings-subtitles-enabled");
                if (subEnabledEl) subEnabledEl.checked = data.SUBTITLES_ENABLED === true;
                const musicEnabledEl = document.getElementById("settings-music-enabled");
                if (musicEnabledEl) musicEnabledEl.checked = data.BACKGROUND_MUSIC_ENABLED !== false;
                
                // BG Music volume slider
                const musicVolEl = document.getElementById("settings-music-volume");
                if (musicVolEl) musicVolEl.value = data.BACKGROUND_MUSIC_VOLUME ?? 0.35;
                const musicVolLbl = document.getElementById("settings-music-volume-lbl");
                if (musicVolLbl) musicVolLbl.textContent = data.BACKGROUND_MUSIC_VOLUME ?? 0.35;

                // Hook Sound Effect & Audio Normalizer
                const hookAudioEl = document.getElementById("settings-hook-audio-enabled");
                if (hookAudioEl) hookAudioEl.checked = data.HOOK_AUDIO_ENABLED === true;
                const hookVolEl = document.getElementById("settings-hook-audio-volume");
                if (hookVolEl) {
                    hookVolEl.value = data.HOOK_AUDIO_VOLUME ?? 0.25;
                    const hookVolLbl = document.getElementById("settings-hook-audio-volume-lbl");
                    if (hookVolLbl) hookVolLbl.textContent = data.HOOK_AUDIO_VOLUME ?? 0.25;
                }
                const audioNormEl = document.getElementById("settings-audio-normalize-enabled");
                if (audioNormEl) audioNormEl.checked = data.AUDIO_NORMALIZE_ENABLED === true;

                // Subtitle custom styles & animation
                const subAnimEl = document.getElementById("settings-subtitle-animation-style");
                if (subAnimEl) subAnimEl.value = data.SUBTITLE_ANIMATION_STYLE || data.SUBTITLE_STYLE?.animation_style || "whisper";
                
                if (document.getElementById("settings-subtitle-font-size")) {
                    document.getElementById("settings-subtitle-font-size").value = data.SUBTITLE_FONT_SIZE ?? 56;
                    document.getElementById("settings-subtitle-font-size-lbl").textContent = data.SUBTITLE_FONT_SIZE ?? 56;
                }
                if (document.getElementById("settings-subtitle-position-y")) {
                    document.getElementById("settings-subtitle-position-y").value = data.SUBTITLE_POSITION_Y ?? 0.68;
                    document.getElementById("settings-subtitle-position-y-lbl").textContent = data.SUBTITLE_POSITION_Y ?? 0.68;
                }
                if (document.getElementById("settings-subtitle-color")) document.getElementById("settings-subtitle-color").value = data.SUBTITLE_COLOR || "#ffffff";
                if (document.getElementById("settings-subtitle-stroke-color")) document.getElementById("settings-subtitle-stroke-color").value = data.SUBTITLE_STROKE_COLOR || "#000000";
                if (document.getElementById("settings-subtitle-stroke-width")) {
                    document.getElementById("settings-subtitle-stroke-width").value = data.SUBTITLE_STROKE_WIDTH ?? 3;
                    document.getElementById("settings-subtitle-stroke-width-lbl").textContent = data.SUBTITLE_STROKE_WIDTH ?? 3;
                }
                if (document.getElementById("settings-subtitle-bg-opacity")) {
                    document.getElementById("settings-subtitle-bg-opacity").value = data.SUBTITLE_BG_OPACITY ?? 148;
                    document.getElementById("settings-subtitle-bg-opacity-lbl").textContent = data.SUBTITLE_BG_OPACITY ?? 148;
                }
                if (document.getElementById("settings-subtitle-max-words")) {
                    document.getElementById("settings-subtitle-max-words").value = data.SUBTITLE_MAX_WORDS_PER_LINE ?? 3;
                    document.getElementById("settings-subtitle-max-words-lbl").textContent = data.SUBTITLE_MAX_WORDS_PER_LINE ?? 3;
                }
                if (document.getElementById("settings-subtitle-karaoke")) document.getElementById("settings-subtitle-karaoke").checked = data.SUBTITLE_KARAOKE !== false;
                if (document.getElementById("settings-subtitle-font-path")) document.getElementById("settings-subtitle-font-path").value = data.SUBTITLE_FONT_PATH || "";

                // Watermark settings
                if (document.getElementById("settings-watermark-enabled")) document.getElementById("settings-watermark-enabled").checked = data.WATERMARK_ENABLED === true;
                if (document.getElementById("settings-watermark-path")) document.getElementById("settings-watermark-path").value = data.WATERMARK_PATH || "assets/watermark.png";
                if (document.getElementById("settings-watermark-position")) document.getElementById("settings-watermark-position").value = data.WATERMARK_POSITION || "right,top";
                document.getElementById("settings-watermark-opacity").value = data.WATERMARK_OPACITY;
                document.getElementById("settings-watermark-opacity-lbl").textContent = data.WATERMARK_OPACITY;
                document.getElementById("settings-watermark-height").value = data.WATERMARK_HEIGHT;
                document.getElementById("settings-watermark-margin").value = data.WATERMARK_MARGIN;

                // Quality preset cards
                loadQualityPresetCards(data.VIDEO_QUALITY_PRESET || "standard");
                
                // API keys
                document.getElementById("key-openai").value = data.api_keys.OPENAI_API_KEY || "";
                document.getElementById("key-cloudflare-account").value = data.api_keys.CLOUDFLARE_ACCOUNT_ID || "";
                document.getElementById("key-cloudflare-token").value = data.api_keys.CLOUDFLARE_API_TOKEN || "";
                document.getElementById("key-groq").value = data.api_keys.GROQ_API_KEY || "";
                document.getElementById("key-gemini").value = data.api_keys.GEMINI_API_KEY || "";
                document.getElementById("key-openrouter").value = data.api_keys.OPENROUTER_API_KEY || "";
                document.getElementById("key-pexels").value = data.api_keys.PEXELS_API_KEY || "";
                document.getElementById("key-pixabay").value = data.api_keys.PIXABAY_API_KEY || "";
                document.getElementById("key-elevenlabs").value = data.api_keys.ELEVENLABS_API_KEY || "";
                document.getElementById("key-puter").value = data.api_keys.PUTER_TOKEN || "";
                // Trending API keys (optional)
                let elNews = document.getElementById("key-newsapi");
                let elGuard = document.getElementById("key-guardian");
                let elGNews = document.getElementById("key-gnews");
                if (elNews) elNews.value = data.api_keys.NEWSAPI_KEY || "";
                if (elGuard) elGuard.value = data.api_keys.GUARDIAN_KEY || "";
                if (elGNews) elGNews.value = data.api_keys.GNEWS_KEY || "";
                
            } catch (e) {
                console.error("Failed to load settings details", e);
                alert("Error loading configurations: " + e.message);
            } finally {
                saveBtn.innerHTML = origHtml;
                saveBtn.disabled = false;
                lucide.createIcons();
            }
        }

        function updateSettingsVoiceDropdown(selectedValue = null) {
            let provider = document.getElementById("settings-tts-provider").value;
            let lang = document.getElementById("settings-lang").value;
            let select = document.getElementById("settings-voice");
            select.innerHTML = "";
            
            if (provider === "direct-gemini") {
                let geminiVoices = [
                    { value: "direct-gemini:Aoede", label: "Aoede (Deep, Natural & Expressive - Recommended)" },
                    { value: "direct-gemini:Puck", label: "Puck (Clear, Dynamic & Engaging)" },
                    { value: "direct-gemini:Zephyr", label: "Zephyr (Peaceful & Warm)" },
                    { value: "direct-gemini:Fenrir", label: "Fenrir (Strong, Powerful & Authoritative)" },
                    { value: "direct-gemini:Kore", label: "Kore (Soft, Gentle & Calm)" },
                    { value: "direct-gemini:Charon", label: "Charon (Resonant & Bold)" }
                ];
                geminiVoices.forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v.value;
                    opt.textContent = v.label;
                    if (selectedValue && (selectedValue === v.value || selectedValue.endsWith(v.value.split(":")[1]))) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            } else if (provider === "elevenlabs") {
                let voices = {
                    "english": [
                        "Rachel (21m00Tcm4TlvDq8ikWAM)",
                        "Drew (29vD33N1CtxCmqQRPOHJ)",
                        "Clyde (2EyyOtef2nt0zpT5pUt5)",
                        "Adam (pNInz6obpgqjVWtJ45dB)",
                        "Nicole (piTKgcLEGmPEe3aY1Z85)",
                        "Bella (EXAVITQu4vr4xnSDxMaL)",
                        "Dom (AZnzlk1XhkjRsfKJHSS0)"
                    ],
                    "swahili": [
                        "Swahili Female (Bella - EXAVITQu4vr4xnSDxMaL)",
                        "Swahili Male (Adam - pNInz6obpgqjVWtJ45dB)"
                    ]
                };
                let list = voices[lang] || voices["english"];
                list.forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v;
                    opt.textContent = v.split(" (")[0];
                    if (selectedValue && v === selectedValue) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            } else if (provider === "puter") {
                const subProviders = ['openai', 'aws-polly', 'elevenlabs', 'gemini', 'xai'];
                subProviders.forEach(sp => {
                    const config = PUTER_PROVIDERS_CONFIG[sp];
                    if (config && config.voices) {
                        config.voices.forEach(v => {
                            let opt = document.createElement("option");
                            opt.value = `puter:${sp}:${v.value}`;
                            opt.textContent = `[${sp.toUpperCase()}] ${v.label}`;
                            if (selectedValue && (selectedValue === opt.value || selectedValue === v.value)) {
                                opt.selected = true;
                            }
                            select.appendChild(opt);
                        });
                    }
                });
            } else {
                // Edge TTS
                let edgeVoices = lang === 'swahili' ? 
                    [{ value: "sw-KE-RafikiNeural", label: "Rafiki (Kenyan Natural Swahili)" }] :
                    [
                        { value: "en-US-ChristopherNeural", label: "Christopher (Deep Gospel / Preacher)" },
                        { value: "en-US-GuyNeural", label: "Guy (Natural Voice)" },
                        { value: "en-US-JennyNeural", label: "Jenny (Warm Female)" },
                        { value: "en-US-AriaNeural", label: "Aria (Expressive Female)" }
                    ];
                edgeVoices.forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v.value;
                    opt.textContent = v.label;
                    if (selectedValue && v.value === selectedValue) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            }
        }


        function onSettingsProviderChanged() {
            updateSettingsVoiceDropdown();
        }

        // Listener for volume slider updates
        document.getElementById("settings-music-volume").addEventListener("input", function(e) {
            document.getElementById("settings-music-volume-lbl").textContent = e.target.value;
        });

        // Subtitle & audio style slider listeners
        const sliders = [
            { id: "settings-hook-audio-volume", lbl: "settings-hook-audio-volume-lbl" },
            { id: "settings-subtitle-font-size", lbl: "settings-subtitle-font-size-lbl" },
            { id: "settings-subtitle-position-y", lbl: "settings-subtitle-position-y-lbl" },
            { id: "settings-subtitle-stroke-width", lbl: "settings-subtitle-stroke-width-lbl" },
            { id: "settings-subtitle-bg-opacity", lbl: "settings-subtitle-bg-opacity-lbl" },
            { id: "settings-subtitle-max-words", lbl: "settings-subtitle-max-words-lbl" },
            { id: "settings-watermark-opacity", lbl: "settings-watermark-opacity-lbl" }
        ];
        sliders.forEach(slider => {
            let el = document.getElementById(slider.id);
            if (el) {
                el.addEventListener("input", function(e) {
                    let lblEl = document.getElementById(slider.lbl);
                    if (lblEl) lblEl.textContent = e.target.value;
                });
            }
        });

        // ── Quality Preset Card Helpers ──
        function loadQualityPresetCards(activePreset) {
            document.querySelectorAll(".quality-preset-card").forEach(card => {
                card.classList.remove("selected");
                if (card.dataset.preset === activePreset) {
                    card.classList.add("selected");
                }
            });
        }

        async function selectQualityPreset(preset) {
            // Update visual selection immediately
            loadQualityPresetCards(preset);
            // Persist to server immediately (fast single-key save)
            try {
                await fetch("/api/settings/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ settings: { VIDEO_QUALITY_PRESET: preset }, api_keys: {} })
                });
            } catch(e) {
                console.warn("Could not persist quality preset:", e);
            }
        }

        async function saveSystemSettings() {
            let saveBtn = document.getElementById("settings-save-btn");
            let origHtml = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Saving...';
            saveBtn.disabled = true;
            lucide.createIcons();

            let settings = {
                NICHE: document.getElementById("settings-niche").value,
                CONTENT_MODE: document.getElementById("settings-content-mode").value,
                LANGUAGE: document.getElementById("settings-lang").value,
                MODE: document.getElementById("settings-mode").value,
                ACTIVE_VOICE: document.getElementById("settings-voice").value,
                TTS_RATE: document.getElementById("settings-tts-rate").value,
                TTS_PITCH: document.getElementById("settings-tts-pitch").value,
                TTS_VOLUME: document.getElementById("settings-tts-volume").value,
                TTS_PROVIDER: document.getElementById("settings-tts-provider").value,
                SUBTITLES_ENABLED: document.getElementById("settings-subtitles-enabled").checked,
                BACKGROUND_MUSIC_ENABLED: document.getElementById("settings-music-enabled").checked,
                BACKGROUND_MUSIC_VOLUME: parseFloat(document.getElementById("settings-music-volume").value),
                HOOK_AUDIO_ENABLED: document.getElementById("settings-hook-audio-enabled")?.checked ?? false,
                HOOK_AUDIO_VOLUME: parseFloat(document.getElementById("settings-hook-audio-volume")?.value ?? 0.25),
                AUDIO_NORMALIZE_ENABLED: document.getElementById("settings-audio-normalize-enabled")?.checked ?? false,
                SUBTITLE_ANIMATION_STYLE: document.getElementById("settings-subtitle-animation-style")?.value || "whisper",
                SUBTITLE_FONT_SIZE: parseInt(document.getElementById("settings-subtitle-font-size").value),
                SUBTITLE_POSITION_Y: parseFloat(document.getElementById("settings-subtitle-position-y").value),
                SUBTITLE_COLOR: document.getElementById("settings-subtitle-color").value.trim(),
                SUBTITLE_STROKE_COLOR: document.getElementById("settings-subtitle-stroke-color").value.trim(),
                SUBTITLE_STROKE_WIDTH: parseInt(document.getElementById("settings-subtitle-stroke-width").value),
                SUBTITLE_BG_OPACITY: parseInt(document.getElementById("settings-subtitle-bg-opacity").value),
                SUBTITLE_MAX_WORDS_PER_LINE: parseInt(document.getElementById("settings-subtitle-max-words").value),
                SUBTITLE_KARAOKE: document.getElementById("settings-subtitle-karaoke").checked,
                SUBTITLE_FONT_PATH: document.getElementById("settings-subtitle-font-path").value.trim(),
                VIDEO_QUALITY_PRESET: document.querySelector(".quality-preset-card.selected")?.dataset?.preset || "standard",
                WATERMARK_ENABLED: document.getElementById("settings-watermark-enabled").checked,
                WATERMARK_PATH: document.getElementById("settings-watermark-path").value.trim(),
                WATERMARK_POSITION: document.getElementById("settings-watermark-position").value,
                WATERMARK_OPACITY: parseFloat(document.getElementById("settings-watermark-opacity").value),
                WATERMARK_HEIGHT: parseInt(document.getElementById("settings-watermark-height").value),
                WATERMARK_MARGIN: parseInt(document.getElementById("settings-watermark-margin").value)
            };

            let api_keys = {
                OPENAI_API_KEY: document.getElementById("key-openai").value.trim(),
                CLOUDFLARE_ACCOUNT_ID: document.getElementById("key-cloudflare-account").value.trim(),
                CLOUDFLARE_API_TOKEN: document.getElementById("key-cloudflare-token").value.trim(),
                GROQ_API_KEY: document.getElementById("key-groq").value.trim(),
                GEMINI_API_KEY: document.getElementById("key-gemini").value.trim(),
                OPENROUTER_API_KEY: document.getElementById("key-openrouter").value.trim(),
                PEXELS_API_KEY: document.getElementById("key-pexels").value.trim(),
                PIXABAY_API_KEY: document.getElementById("key-pixabay").value.trim(),
                ELEVENLABS_API_KEY: document.getElementById("key-elevenlabs").value.trim(),
                NEWSAPI_KEY: (document.getElementById("key-newsapi")?.value || "").trim(),
                GUARDIAN_KEY: (document.getElementById("key-guardian")?.value || "").trim(),
                GNEWS_KEY: (document.getElementById("key-gnews")?.value || "").trim(),
                PUTER_TOKEN: document.getElementById("key-puter").value.trim()
            };

            try {
                let res = await fetch("/api/settings/save", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ settings, api_keys })
                });

                if (res.ok) {
                    alert("Configurations saved successfully! Backend settings have been reloaded.");
                    // Refresh creator configs in-memory
                    await loadConfig();
                    updateVoiceOptions();
                } else {
                    let err = await res.json();
                    alert("Save failed: " + err.detail);
                }
            } catch (e) {
                alert("Connection failed: " + e.message);
            } finally {
                saveBtn.innerHTML = origHtml;
                saveBtn.disabled = false;
                lucide.createIcons();
            }
        }



        // ============================================================
        // MULTI-PROVIDER VOICE STUDIO FRONTEND LOGIC
        // ============================================================
        let ttsCompareList = [];
        let currentPuterSubProvider = 'aws-polly';
        let audioCtx = null;
        let analyser = null;
        let sourceNode = null;
        let visualizerAnimationId = null;



        async function initExplorerTTS() {
            if (!currentConfig || !currentConfig.voices) {
                await loadConfig();
            }
            
            // Draw static waveform once at start
            const canvas = document.getElementById("waveform-canvas");
            if (canvas) {
                const ctx = canvas.getContext("2d");
                drawStaticWaveform(ctx, canvas.width, canvas.height);
            }
            
            // Setup Web Audio nodes on player
            setupAudioVisualizer();
            
            // Populate dropdown values
            onExplorerProviderChanged();
            
            // Load side-by-side comparison list
            loadCompareList();
        }

        function selectExplorerProvider(provider) {
            // Update active status on buttons
            document.querySelectorAll(".provider-btn").forEach(btn => btn.classList.remove("active"));
            if (provider === 'edge-tts') document.getElementById("btn-prov-edge").classList.add("active");
            if (provider === 'elevenlabs') document.getElementById("btn-prov-eleven").classList.add("active");
            if (provider === 'puter') document.getElementById("btn-prov-puter").classList.add("active");

            // Sync hidden inputs for compatibility
            document.getElementById("tts-explorer-provider").value = provider;
            
            onExplorerProviderChanged();
        }
        window.selectExplorerProvider = selectExplorerProvider;

        function selectPuterSubProvider(subProvider) {
            document.querySelectorAll(".sub-provider-btn").forEach(btn => btn.classList.remove("active"));
            if (subProvider === 'aws-polly') document.getElementById("btn-puter-aws").classList.add("active");
            if (subProvider === 'openai') document.getElementById("btn-puter-openai").classList.add("active");
            if (subProvider === 'elevenlabs') document.getElementById("btn-puter-eleven").classList.add("active");
            if (subProvider === 'gemini') document.getElementById("btn-puter-gemini").classList.add("active");
            if (subProvider === 'xai') document.getElementById("btn-puter-xai").classList.add("active");

            currentPuterSubProvider = subProvider;
            onExplorerProviderChanged();
        }
        window.selectPuterSubProvider = selectPuterSubProvider;

        function updateFineTuningValues() {
            const speed = parseFloat(document.getElementById("tts-explorer-rate-slider").value);
            const pitch = parseFloat(document.getElementById("tts-explorer-pitch-slider").value);
            
            document.getElementById("rate-slider-val").textContent = speed.toFixed(2) + "x";
            document.getElementById("pitch-slider-val").textContent = pitch.toFixed(2) + "x";
        }

        function onExplorerProviderChanged() {
            let provider = document.getElementById("tts-explorer-provider").value;
            let selectVoice = document.getElementById("tts-explorer-voice");
            let selectEngine = document.getElementById("tts-explorer-engine");
            let selectModel = document.getElementById("tts-explorer-model");
            let selectFormat = document.getElementById("tts-explorer-format");
            
            // Clear selections
            selectVoice.innerHTML = "";
            selectEngine.innerHTML = "";
            selectModel.innerHTML = "";
            selectFormat.innerHTML = "";

            // Hide/Show Puter Sub-provider bar
            const puterGroup = document.getElementById("puter-sub-provider-group");
            const engineGroup = document.getElementById("explorer-engine-group");
            const modelGroup = document.getElementById("explorer-model-group");
            const formatGroup = document.getElementById("explorer-format-group");
            const instGroup = document.getElementById("explorer-instructions-group");
            
            puterGroup.style.display = "none";
            engineGroup.style.display = "none";
            modelGroup.style.display = "none";
            formatGroup.style.display = "none";
            instGroup.style.display = "none";

            if (provider === "elevenlabs") {
                let voices = [
                    "Rachel (21m00Tcm4TlvDq8ikWAM)",
                    "Drew (29vD33N1CtxCmqQRPOHJ)",
                    "Clyde (2EyyOtef2nt0zpT5pUt5)",
                    "Adam (pNInz6obpgqjVWtJ45dB)",
                    "Nicole (piTKgcLEGmPEe3aY1Z85)",
                    "Bella (EXAVITQu4vr4xnSDxMaL)",
                    "Dom (AZnzlk1XhkjRsfKJHSS0)"
                ];
                voices.forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v;
                    opt.textContent = v.split(" (")[0];
                    selectVoice.appendChild(opt);
                });
            } else if (provider === "puter") {
                puterGroup.style.display = "block";
                const config = PUTER_PROVIDERS_CONFIG[currentPuterSubProvider] || PUTER_PROVIDERS_CONFIG['openai'];
                
                // Populate voices
                config.voices.forEach(v => {
                    let opt = document.createElement("option");
                    opt.value = v.value;
                    opt.textContent = v.label;
                    selectVoice.appendChild(opt);
                });

                // Populate engines
                if (config.engines) {
                    engineGroup.style.display = "flex";
                    document.getElementById("explorer-engine-label").textContent = "Engine Type";
                    config.engines.forEach(e => {
                        let opt = document.createElement("option");
                        opt.value = e.value;
                        opt.textContent = e.label;
                        selectEngine.appendChild(opt);
                    });
                }

                // Populate models
                if (config.models) {
                    modelGroup.style.display = "flex";
                    // For AWS Polly & xAI, models acts as languages select
                    if (currentPuterSubProvider === 'aws-polly' || currentPuterSubProvider === 'xai') {
                        document.getElementById("explorer-model-label").textContent = "Language";
                    } else {
                        document.getElementById("explorer-model-label").textContent = "Model Option";
                    }
                    config.models.forEach(m => {
                        let opt = document.createElement("option");
                        opt.value = m.value;
                        opt.textContent = m.label;
                        selectModel.appendChild(opt);
                    });
                }

                // Populate formats
                if (config.formats) {
                    formatGroup.style.display = "flex";
                    document.getElementById("explorer-format-label").textContent = "Output Format";
                    config.formats.forEach(f => {
                        let opt = document.createElement("option");
                        opt.value = f.value;
                        opt.textContent = f.label;
                        selectFormat.appendChild(opt);
                    });
                }

                // Show instructions text area for OpenAI/Gemini
                if (currentPuterSubProvider === 'openai' || currentPuterSubProvider === 'gemini') {
                    instGroup.style.display = "flex";
                }

            } else { // edge-tts
                if (currentConfig.voices) {
                    let allEdgeVoices = [];
                    if (currentConfig.voices.english) allEdgeVoices.push(...currentConfig.voices.english);
                    if (currentConfig.voices.swahili) allEdgeVoices.push(...currentConfig.voices.swahili);
                    
                    allEdgeVoices.forEach(v => {
                        let opt = document.createElement("option");
                        opt.value = v;
                        opt.textContent = v.split("-")[2].replace("Neural", "") + ` (${v.split("-")[0]}-${v.split("-")[1]})`;
                        selectVoice.appendChild(opt);
                    });
                }
            }
        }

        async function playExplorerTTS() {
            let provider = document.getElementById("tts-explorer-provider").value;
            let voice = document.getElementById("tts-explorer-voice").value;
            let text = document.getElementById("tts-explorer-text").value.trim();
            
            if (!text) {
                alert("Please type some test text to read!");
                return;
            }

            let btn = document.getElementById("tts-explorer-btn");
            let origHtml = btn.innerHTML;
            btn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Generating...';
            btn.disabled = true;
            lucide.createIcons();

            let objectUrl = null;

            try {
                let player = document.getElementById("tts-audio-player");
                
                const rawSpeed = parseFloat(document.getElementById("tts-explorer-rate-slider").value);
                const rawPitch = parseFloat(document.getElementById("tts-explorer-pitch-slider").value);
                
                const ratePct = (rawSpeed >= 1.0 ? "+" : "") + Math.round((rawSpeed - 1.0) * 100) + "%";
                const pitchHz = (rawPitch >= 1.0 ? "+" : "") + Math.round((rawPitch - 1.0) * 10) + "Hz";
                const volumeStr = "+0%";
                
                // For Puter, prefix voice with sub-provider for backend parsing
                if (provider === "puter") {
                    voice = `puter:${currentPuterSubProvider}:${voice}`;
                }
                let previewUrl = `/api/tts/preview?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(ratePct)}&pitch=${encodeURIComponent(pitchHz)}&volume=${encodeURIComponent(volumeStr)}`;
                
                // Append extra Puter sub-provider options
                if (provider === "puter") {
                    const engineVal = document.getElementById("tts-explorer-engine")?.value;
                    const modelVal = document.getElementById("tts-explorer-model")?.value;
                    const formatVal = document.getElementById("tts-explorer-format")?.value;
                    const instVal = document.getElementById("tts-explorer-instructions")?.value.trim();
                    if (engineVal) previewUrl += `&puter_engine=${encodeURIComponent(engineVal)}`;
                    if (modelVal) previewUrl += `&puter_model=${encodeURIComponent(modelVal)}`;
                    if (formatVal) previewUrl += `&puter_format=${encodeURIComponent(formatVal)}`;
                    if (instVal) previewUrl += `&puter_instructions=${encodeURIComponent(instVal)}`;
                }

                player.src = `${previewUrl}&_t=${Date.now()}`;

                player.onerror = function() {
                    alert("Audio playback failed. Check your TTS provider settings.");
                    btn.innerHTML = origHtml;
                    btn.disabled = false;
                    lucide.createIcons();
                };

                await player.play();
            } catch (e) {
                console.error("Audio preview failed", e);
                alert("Audio preview generation failed: " + e.message);
            } finally {
                btn.innerHTML = origHtml;
                btn.disabled = false;
                lucide.createIcons();
            }

            if (objectUrl) {
                const player = document.getElementById("tts-audio-player");
                const oldended = player.onended;
                player.onended = function() {
                    if (oldended) oldended();
                    try { URL.revokeObjectURL(objectUrl); } catch(e){}
                };
            }
        }
        window.playExplorerTTS = playExplorerTTS;

        // ============================================================
        // CANVAS WAVEFORM VISUALIZER LOGIC (WEB AUDIO API)
        // ============================================================
        function setupAudioVisualizer() {
            const player = document.getElementById("tts-audio-player");
            const canvas = document.getElementById("waveform-canvas");
            const statusLbl = document.getElementById("visualizer-status");
            if (!canvas || !player) return;
            
            const ctx = canvas.getContext("2d");
            if (player._vfVisualizerAttached) return;
            player._vfVisualizerAttached = true;
            
            player.addEventListener("play", () => {
                if (statusLbl) {
                    statusLbl.textContent = "Playing...";
                    statusLbl.style.color = "var(--accent-success)";
                }
                
                try {
                    if (!audioCtx) {
                        const AC = window.AudioContext || window.webkitAudioContext;
                        if (AC) {
                            audioCtx = new AC({ latencyHint: "playback" });
                            analyser = audioCtx.createAnalyser();
                            analyser.fftSize = 128;
                            
                            if (!player._sourceNodeAttached) {
                                sourceNode = audioCtx.createMediaElementSource(player);
                                sourceNode.connect(analyser);
                                analyser.connect(audioCtx.destination);
                                player._sourceNodeAttached = true;
                            }
                        }
                    }
                    
                    if (audioCtx && audioCtx.state === 'suspended') {
                        audioCtx.resume();
                    }
                    
                    // Start animation drawing loop
                    if (visualizerAnimationId) cancelAnimationFrame(visualizerAnimationId);
                    drawVisualizer();
                } catch (err) {
                    console.warn("AudioContext setup note (direct playback fallback active):", err);
                }
            });
            
            player.addEventListener("pause", () => {
                if (statusLbl) {
                    statusLbl.textContent = "Paused";
                    statusLbl.style.color = "var(--text-muted)";
                }
                if (visualizerAnimationId) {
                    cancelAnimationFrame(visualizerAnimationId);
                }
            });
            
            player.addEventListener("ended", () => {
                if (statusLbl) {
                    statusLbl.textContent = "Ended";
                    statusLbl.style.color = "var(--text-muted)";
                }
                if (visualizerAnimationId) {
                    cancelAnimationFrame(visualizerAnimationId);
                }
                drawStaticWaveform(ctx, canvas.width, canvas.height);
            });
        }

        function drawVisualizer() {
            const canvas = document.getElementById("waveform-canvas");
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            const width = canvas.width;
            const height = canvas.height;
            
            if (!analyser) return;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            function draw() {
                visualizerAnimationId = requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);
                
                ctx.fillStyle = "rgba(3, 0, 20, 0.2)"; // base background trail
                ctx.fillRect(0, 0, width, height);
                
                const barWidth = (width / bufferLength) * 1.5;
                let x = 0;
                
                for (let i = 0; i < bufferLength; i++) {
                    const barHeight = (dataArray[i] / 255) * height * 0.8;
                    
                    const gradient = ctx.createLinearGradient(0, height, 0, height - barHeight);
                    gradient.addColorStop(0, '#a855f7'); // purple
                    gradient.addColorStop(1, '#06b6d4'); // cyan
                    
                    ctx.fillStyle = gradient;
                    const y = height/2 - barHeight/2;
                    ctx.fillRect(x, y, barWidth - 1, barHeight + 2);
                    
                    x += barWidth;
                }
            }
            
            draw();
        }

        function drawStaticWaveform(ctx, width, height) {
            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = "rgba(3, 0, 20, 1)";
            ctx.fillRect(0, 0, width, height);
            
            ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, height / 2);
            for (let x = 0; x < width; x += 10) {
                const y = height / 2 + Math.sin(x * 0.05) * 4;
                ctx.lineTo(x, y);
            }
            ctx.stroke();
        }

        function loadCompareList() {
            try {
                let stored = localStorage.getItem("videofactory_tts_compare");
                if (stored) {
                    ttsCompareList = JSON.parse(stored);
                } else {
                    ttsCompareList = [];
                }
            } catch (e) {
                console.error(e);
                ttsCompareList = [];
            }
            renderCompareList();
        }

        function saveCompareList() {
            localStorage.setItem("videofactory_tts_compare", JSON.stringify(ttsCompareList));
        }

        function addToCompareList() {
            let provider = document.getElementById("tts-explorer-provider").value;
            let voice = document.getElementById("tts-explorer-voice").value;
            let text = document.getElementById("tts-explorer-text").value.trim();
            
            if (!text) {
                alert("Please type some text first!");
                return;
            }

            const rawSpeed = parseFloat(document.getElementById("tts-explorer-rate-slider").value);
            const rawPitch = parseFloat(document.getElementById("tts-explorer-pitch-slider").value);
            
            const rateStr = rawSpeed.toFixed(2) + "x";
            const pitchStr = rawPitch.toFixed(2) + "x";
            
            let displayProvider = provider;
            let displayVoice = voice;
            let saveVoice = voice;
            
            if (provider === "puter") {
                displayProvider = `Puter (${currentPuterSubProvider})`;
                saveVoice = `puter:${currentPuterSubProvider}:${voice}`;
            } else if (provider === "edge-tts") {
                displayProvider = "Edge-TTS";
            } else {
                displayProvider = "ElevenLabs";
            }
            
            let item = {
                id: "compare_" + Date.now(),
                provider: provider,
                subProvider: currentPuterSubProvider,
                displayProvider: displayProvider,
                voice: saveVoice,
                rate: rateStr,
                pitch: pitchStr,
                volume: "1.0x",
                text: text
            };
            
            ttsCompareList.push(item);
            saveCompareList();
            renderCompareList();
            alert("Added to side-by-side comparison list!");
        }

        function deleteCompareItem(id) {
            ttsCompareList = ttsCompareList.filter(item => item.id !== id);
            saveCompareList();
            renderCompareList();
        }

        function clearCompareList() {
            if (confirm("Are you sure you want to clear the comparison history?")) {
                ttsCompareList = [];
                saveCompareList();
                renderCompareList();
            }
        }

        async function playCompareItem(id) {
            let item = ttsCompareList.find(x => x.id === id);
            if (!item) return;
            
            let player = document.getElementById("tts-audio-player");
            let btn = document.getElementById("tts-explorer-btn");
            let origHtml = btn ? btn.innerHTML : "Play";
            
            if (btn) {
                btn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Previewing compare...';
                btn.disabled = true;
                lucide.createIcons();
            }

            let objectUrl = null;

            try {
                if (item.provider === "puter") {
                    const rawSpeed = parseFloat(item.rate.replace("x", ""));
                    const rawPitch = parseFloat(item.pitch.replace("x", ""));
                    const ratePct = (rawSpeed >= 1.0 ? "+" : "") + Math.round((rawSpeed - 1.0) * 100) + "%";
                    const pitchHz = (rawPitch >= 1.0 ? "+" : "") + Math.round((rawPitch - 1.0) * 10) + "Hz";
                    let previewUrl = `/api/tts/preview?text=${encodeURIComponent(item.text)}&voice=${encodeURIComponent(item.voice)}&rate=${encodeURIComponent(ratePct)}&pitch=${encodeURIComponent(pitchHz)}&volume=+0%`;
                    if (item.subProvider === 'aws-polly') {
                        previewUrl += `&puter_engine=neural&puter_model=en-US`;
                    }
                    player.src = `${previewUrl}&_t=${Date.now()}`;
                    await player.play();
                } else {
                    const rawSpeed = parseFloat(item.rate.replace("x", ""));
                    const rawPitch = parseFloat(item.pitch.replace("x", ""));
                    
                    const ratePct = (rawSpeed >= 1.0 ? "+" : "") + Math.round((rawSpeed - 1.0) * 100) + "%";
                    const pitchHz = (rawPitch >= 1.0 ? "+" : "") + Math.round((rawPitch - 1.0) * 10) + "Hz";
                    const volumeStr = "+0%";
                    
                    let previewUrl = `/api/tts/preview?text=${encodeURIComponent(item.text)}&voice=${encodeURIComponent(item.voice)}&rate=${encodeURIComponent(ratePct)}&pitch=${encodeURIComponent(pitchHz)}&volume=${encodeURIComponent(volumeStr)}`;
                    player.src = `${previewUrl}&_t=${Date.now()}`;
                    await player.play();
                }
            } catch (e) {
                alert("Playback failed: " + e.message);
            } finally {
                if (btn) {
                    btn.innerHTML = origHtml;
                    btn.disabled = false;
                    lucide.createIcons();
                }
            }

            if (objectUrl) {
                const oldended = player.onended;
                player.onended = function() {
                    if (oldended) oldended();
                    try { URL.revokeObjectURL(objectUrl); } catch(e){}
                };
            }
        }

        function renderCompareList() {
            let tbody = document.getElementById("tts-compare-body");
            if (!tbody) return;
            
            tbody.innerHTML = "";
            
            if (ttsCompareList.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="padding: 2rem; text-align: center; color: var(--text-muted);">No voices in comparison list. Add a voice from the sandbox above to compare.</td>
                    </tr>
                `;
                return;
            }
            
            ttsCompareList.forEach(item => {
                let tr = document.createElement("tr");
                
                let voiceName = item.voice;
                if (voiceName.includes("(")) voiceName = voiceName.split(" (")[0];
                if (voiceName.includes("-")) voiceName = voiceName.split("-")[2].replace("Neural", "");
                
                let textSnippet = item.text.length > 50 ? item.text.substring(0, 50) + "..." : item.text;
                
                tr.innerHTML = `
                    <td style="font-weight: 700; color: #a855f7;">${voiceName}</td>
                    <td>
                        <span style="font-size: 0.75rem; font-weight: 700; background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.3); color: #22d3ee; padding: 0.15rem 0.5rem; border-radius: 4px;">
                            ${item.displayProvider}
                        </span>
                    </td>
                    <td>${item.rate}</td>
                    <td>${item.pitch}</td>
                    <td>${item.volume}</td>
                    <td style="font-style: italic; color: var(--text-muted);" title="${item.text}">${textSnippet}</td>
                    <td>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; display: flex; align-items: center; gap: 0.25rem;" onclick="playCompareItem('${item.id}')">
                                <i data-lucide="play" style="width: 12px; height: 12px;"></i> Play
                            </button>
                            <button class="btn btn-secondary btn-circle" style="background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.2); color: var(--accent-error);" onclick="deleteCompareItem('${item.id}')">
                                <i data-lucide="trash-2" style="width: 12px; height: 12px;"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();
        }

        async function saveSystemSettingsSilently(token) {
            try {
                let res = await fetch("/api/settings");
                if (res.ok) {
                    let settingsData = await res.json();
                    await fetch("/api/settings/save", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({
                            settings: {
                                NICHE: settingsData.NICHE,
                                CONTENT_MODE: settingsData.CONTENT_MODE,
                                LANGUAGE: settingsData.LANGUAGE,
                                MODE: settingsData.MODE,
                                ACTIVE_VOICE: settingsData.ACTIVE_VOICE,
                                PUTER_TOKEN: token,
                                TTS_PROVIDER: "puter",
                                TTS_RATE: settingsData.TTS_RATE,
                                TTS_PITCH: settingsData.TTS_PITCH,
                                TTS_VOLUME: settingsData.TTS_VOLUME,
                                SUBTITLES_ENABLED: settingsData.SUBTITLES_ENABLED,
                                BACKGROUND_MUSIC_ENABLED: settingsData.BACKGROUND_MUSIC_ENABLED,
                                BACKGROUND_MUSIC_VOLUME: settingsData.BACKGROUND_MUSIC_VOLUME
                            },
                            api_keys: {
                                ...settingsData.api_keys,
                                PUTER_TOKEN: token
                            }
                        })
                    });
                    await loadConfig();
                    updateVoiceOptions();
                    
                    let provInput = document.getElementById("settings-tts-provider");
                    if (provInput) provInput.value = "puter";
                    updateSettingsVoiceDropdown();
                }
            } catch (e) {
                console.error("Silent settings save failed:", e);
            }
        }

        async function autoSyncPuterToken() {
            try {
                let res = await fetch("/api/settings");
                if (res.ok) {
                    let settingsData = await res.json();
                    let backendToken = settingsData.api_keys ? settingsData.api_keys.PUTER_TOKEN : "";
                    if (!backendToken) {
                        let localToken = null;
                        if (typeof puter !== 'undefined' && puter.authToken) {
                            localToken = puter.authToken;
                        }
                        if (!localToken) {
                            localToken = localStorage.getItem('puter.auth.token') || 
                                         localStorage.getItem('puter-auth-token') || 
                                         localStorage.getItem('puter-token') ||
                                         localStorage.getItem('puter.authToken');
                        }
                        if (!localToken && typeof puter !== 'undefined' && puter.auth && typeof puter.auth.getAuthToken === 'function') {
                            localToken = puter.auth.getAuthToken();
                        }
                        
                        if (localToken && localToken.trim()) {
                            console.log("Auto-syncing Puter Token to backend...");
                            await saveSystemSettingsSilently(localToken.trim());
                            let puterKeyInput = document.getElementById("key-puter");
                            if (puterKeyInput) puterKeyInput.value = localToken.trim();
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to auto-sync Puter token:", e);
            }
        }

        async function loginWithPuter() {
            if (typeof puter === 'undefined') {
                alert("Puter SDK is loading, please wait...");
                return;
            }
            // Monkeypatch getAuthToken if it doesn't exist to prevent crash inside puter.auth.signIn()
            if (puter.auth && typeof puter.auth.getAuthToken !== 'function') {
                puter.auth.getAuthToken = function() {
                    return puter.authToken || localStorage.getItem('puter.auth.token') || localStorage.getItem('puter-auth-token') || localStorage.getItem('puter-token');
                };
            }
            try {
                await puter.auth.signIn();
                const token = puter.authToken || localStorage.getItem('puter.auth.token') || localStorage.getItem('puter-auth-token') || localStorage.getItem('puter-token');
                if (token) {
                    document.getElementById("key-puter").value = token;
                    await saveSystemSettingsSilently(token);
                    alert("Successfully authenticated with Puter! Settings saved.");
                } else {
                    alert("Could not retrieve authentication token.");
                }
            } catch (e) {
                alert("Puter Authentication failed: " + e.message);
            }
        }

        // Run Init
        init();

// Mobile Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('mobile-open');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.querySelector('.mobile-nav-toggle');
    
    if (window.innerWidth <= 1100 && sidebar && sidebar.classList.contains('mobile-open')) {
        if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target)) {
            sidebar.classList.remove('mobile-open');
        }
    }
});


/* =========================================
   FURTHER ADVANCED JS LOGIC (V3)
   ========================================= */

// Command Palette Logic
const cmdPalette = document.getElementById('cmd-palette');
const cmdOverlay = document.getElementById('cmd-overlay');
const cmdInput = document.getElementById('cmd-input');
const cmdResults = document.querySelectorAll('.cmd-item');

function toggleCmdPalette() {
    if (!cmdPalette) return;
    const isOpen = cmdPalette.classList.contains('open');
    if (isOpen) {
        cmdPalette.classList.remove('open');
        cmdOverlay.classList.remove('open');
        cmdInput.blur();
    } else {
        cmdPalette.classList.add('open');
        cmdOverlay.classList.add('open');
        cmdInput.value = '';
        cmdInput.focus();
        filterCmd('');
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+K or Cmd+K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        toggleCmdPalette();
    }
    // Escape to close
    if (e.key === 'Escape') {
        if (cmdPalette && cmdPalette.classList.contains('open')) {
            toggleCmdPalette();
        }
    }
});

// Click outside to close
if (cmdOverlay) {
    cmdOverlay.addEventListener('click', toggleCmdPalette);
}

// Filtering commands
if (cmdInput) {
    cmdInput.addEventListener('input', (e) => {
        filterCmd(e.target.value.toLowerCase());
    });
}

function filterCmd(query) {
    cmdResults.forEach(item => {
        if (item.textContent.toLowerCase().includes(query)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Sidebar Active Indicator Logic
function updateSidebarIndicator() {
    const navList = document.querySelector('.nav-list');
    const activeItem = document.querySelector('.nav-item.active');
    if (!navList || !activeItem) return;

    let indicator = document.querySelector('.nav-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'nav-indicator';
        navList.appendChild(indicator);
    }

    const offsetTop = activeItem.offsetTop;
    indicator.style.transform = `translateY(${offsetTop}px)`;
}

// Hook into existing switchTab function safely
const originalSwitchTab = window.switchTab;
if (typeof originalSwitchTab === 'function') {
    window.switchTab = function(tabId) {
        originalSwitchTab(tabId);
        setTimeout(updateSidebarIndicator, 50); // slight delay to allow active class update
    };
} else {
    // Fallback if switchTab isn't global yet
    setTimeout(updateSidebarIndicator, 500);
}

// Initial setup on load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(updateSidebarIndicator, 100);
    // Initialize lucide icons if available
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});


// ═══════════════════════════════════════════════════════════════
// VOICE LAB — TTS Voice Explorer
// ═══════════════════════════════════════════════════════════════

let _vlabAllVoices = [];
let _vlabCurrentVoice = null;

// Called by switchTab('tts')
function initExplorerTTS() {
    if (_vlabAllVoices.length === 0) {
        vlabLoadVoices(false);
    } else {
        vlabFilterVoices();
    }
}

async function vlabLoadVoices(forceRefresh = false) {
    const grid    = document.getElementById('vlab-grid');
    const loading = document.getElementById('vlab-loading');
    const empty   = document.getElementById('vlab-empty');
    const count   = document.getElementById('vlab-count');
    const btn     = document.getElementById('vlab-refresh-btn');

    loading.style.display = 'block';
    grid.style.display    = 'none';
    empty.style.display   = 'none';
    count.textContent     = 'Loading…';
    if (btn) btn.disabled = true;

    try {
        const url = forceRefresh ? '/api/tts/voices?force_refresh=true' : '/api/tts/voices';
        const res  = await fetch(url);
        const data = await res.json();
        _vlabAllVoices = data.voices || [];
        vlabFilterVoices();
    } catch(e) {
        count.textContent = 'Error loading';
        loading.innerHTML = `<p style="color:var(--accent-error)">Failed to load voices: ${e.message}</p>`;
    } finally {
        if (btn) btn.disabled = false;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

function vlabFilterVoices() {
    const lang     = (document.getElementById('vlab-lang')?.value     || '').toLowerCase();
    const provider = (document.getElementById('vlab-provider')?.value || '').toLowerCase();
    const gender   = (document.getElementById('vlab-gender')?.value   || '');

    const filtered = _vlabAllVoices.filter(v => {
        if (lang     && !v.lang_code.toLowerCase().startsWith(lang))       return false;
        if (provider && v.provider.toLowerCase() !== provider)              return false;
        if (gender   && v.gender !== gender)                                return false;
        return true;
    });

    vlabRenderVoices(filtered);
}

function vlabRenderVoices(voices) {
    const grid    = document.getElementById('vlab-grid');
    const loading = document.getElementById('vlab-loading');
    const empty   = document.getElementById('vlab-empty');
    const count   = document.getElementById('vlab-count');

    loading.style.display = 'none';

    if (!voices || voices.length === 0) {
        grid.style.display  = 'none';
        empty.style.display = 'block';
        count.textContent   = '0 voices';
        return;
    }

    count.textContent   = `${voices.length} voices`;
    empty.style.display = 'none';
    grid.style.display  = 'grid';

    const providerColors = {
        'edge-tts':     '#10b981',
        'puter':        '#8b5cf6',
        'elevenlabs':   '#f59e0b',
        'direct-gemini':'#3b82f6',
    };

    grid.innerHTML = voices.map(v => {
        const color  = providerColors[v.provider] || '#6b7280';
        const isFree = v.is_free ? '<span style="font-size:0.7rem; background:#10b98122; color:#10b981; padding:0.1rem 0.4rem; border-radius:8px; margin-left:0.4rem;">FREE</span>' : '';
        const gIcon  = v.gender === 'Female' ? '♀' : v.gender === 'Male' ? '♂' : '⚡';
        return `
        <div class="glass-card" style="padding: 0.9rem 1rem; cursor:pointer; border: 1px solid var(--border-subtle); transition: border-color 0.2s;"
             onmouseover="this.style.borderColor='${color}'"
             onmouseout="this.style.borderColor='var(--border-subtle)'"
             onclick="vlabPreview('${v.voice_id.replace(/'/g,"\\'")}', '${v.display_name.replace(/'/g,"\\'")}')">
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:0.5rem;">
                <div style="flex:1; min-width:0;">
                    <div style="font-size:0.75rem; color:${color}; font-weight:600; margin-bottom:0.2rem; text-transform:uppercase; letter-spacing:0.05em;">
                        ${v.provider} ${isFree}
                    </div>
                    <div style="font-size:0.9rem; font-weight:600; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${v.display_name}">
                        ${v.display_name.replace(/\[.*?\]\s*/,'').trim()}
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.15rem;">
                        ${gIcon} ${v.gender} · ${v.language}
                    </div>
                </div>
                <button title="Preview this voice"
                        style="background:${color}22; border:none; border-radius:8px; padding:0.4rem 0.6rem; cursor:pointer; color:${color}; font-size:1rem; flex-shrink:0;"
                        onclick="event.stopPropagation(); vlabPreview('${v.voice_id.replace(/'/g,"\\'")}', '${v.display_name.replace(/'/g,"\\'")}')">
                    ▶
                </button>
            </div>
        </div>`;
    }).join('');

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function vlabPreview(voiceId, displayName) {
    const text = (document.getElementById('vlab-preview-text')?.value || '').trim()
                 || 'Mungu hakusahau. Amini Yeye leo.';
    const playerSection = document.getElementById('vlab-player-section');
    const playingVoice  = document.getElementById('vlab-playing-voice');
    const playingLabel  = document.getElementById('vlab-playing-label');
    const audio         = document.getElementById('vlab-audio');
    const useBtn        = document.getElementById('vlab-use-btn');

    playingLabel.textContent = 'Generating preview…';
    playingVoice.textContent = displayName;
    playerSection.style.display = 'flex';
    if (audio) { audio.src = ''; audio.pause(); }
    if (useBtn) useBtn.style.display = 'none';

    try {
        const res  = await fetch('/api/tts/preview', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ voice: voiceId, text })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        audio.src = data.audio_url + '?t=' + Date.now();
        audio.play().catch(() => {});
        playingLabel.textContent = 'Now previewing:';
        _vlabCurrentVoice = { voice_id: voiceId, display_name: displayName };
        if (useBtn) useBtn.style.display = 'inline-flex';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch(e) {
        playingLabel.textContent = 'Preview failed:';
        playingVoice.textContent = e.message;
        playingVoice.style.color = 'var(--accent-error)';
        setTimeout(() => { playingVoice.style.color = ''; }, 3000);
    }
}

async function vlabUseThisVoice() {
    if (!_vlabCurrentVoice) return;
    const { voice_id, display_name } = _vlabCurrentVoice;

    try {
        // Save to server settings
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ active_voice: voice_id })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        // Also update the voice dropdown in Script Creator
        const voiceSelect = document.getElementById('script-voice');
        if (voiceSelect) {
            let opt = voiceSelect.querySelector(`option[value="${voice_id}"]`);
            if (!opt) {
                opt = document.createElement('option');
                opt.value = voice_id;
                voiceSelect.appendChild(opt);
            }
            opt.textContent = `★ ${display_name}`;
            voiceSelect.value = voice_id;
        }

        // Visual confirmation
        const useBtn = document.getElementById('vlab-use-btn');
        if (useBtn) {
            const orig = useBtn.innerHTML;
            useBtn.innerHTML = '<i data-lucide="check"></i> Voice Set!';
            useBtn.style.background = 'var(--accent-success)';
            setTimeout(() => {
                useBtn.innerHTML = orig;
                useBtn.style.background = '';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }, 2000);
        }
    } catch(e) {
        alert('Could not set voice: ' + e.message);
    }
}

// ═══════════════════════════════════════════════════════════════
// SONG TO REEL (LYRICS MODE)
// ═══════════════════════════════════════════════════════════════

function onLyricsModeChanged() {
    let mode = document.getElementById("lyrics-input-mode").value;
    let group = document.getElementById("group-custom-lyrics");
    if (mode === "custom") {
        group.style.display = "block";
    } else {
        group.style.display = "none";
    }
}
window.onLyricsModeChanged = onLyricsModeChanged;

const EQ_FREQS = [60, 250, 1000, 4000, 12000];

class VideoFactoryAudioEngine {
    constructor() {
        this.ctx = null;
        this.source = null;
        this.filters = [];
        this.bass = null;
        this.compressor = null;
        this.master = null;
        this.analyser = null;
        this.el = null;
        this.built = false;
        this.animId = 0;
        this.currentPreset = "flat";
    }

    resume() {
        if (this.ctx && this.ctx.state === "suspended") {
            this.ctx.resume().catch(() => {});
        }
    }

    attach(el) {
        if (!el) return;
        this.el = el;
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;

        try {
            if (!this.ctx) {
                this.ctx = new AC({ latencyHint: "playback" });
            }
            const ctx = this.ctx;

            // Auto resume on playback events
            if (!el._vfPlayListenerAdded) {
                el._vfPlayListenerAdded = true;
                el.addEventListener("play", () => this.resume());
                el.addEventListener("playing", () => this.resume());
            }

            if (el._vfSourceAttached || this.built) return;

            this.source = ctx.createMediaElementSource(el);
            el._vfSourceAttached = true;

            // 1. Create 5-Band Equalizer - Neutral 0dB default
            this.filters = EQ_FREQS.map((freq, i) => {
                const filter = ctx.createBiquadFilter();
                filter.type = i === 0 ? "lowshelf" : i === EQ_FREQS.length - 1 ? "highshelf" : "peaking";
                filter.frequency.value = freq;
                filter.Q.value = 1.0;
                filter.gain.value = 0.0;
                return filter;
            });

            // 2. Bass Boost (Low-Shelf at 120Hz) - Neutral 0dB default
            this.bass = ctx.createBiquadFilter();
            this.bass.type = "lowshelf";
            this.bass.frequency.value = 120;
            this.bass.gain.value = 0.0;

            // 3. Dynamics Compressor - Off by default (0dB threshold = transparent)
            this.compressor = ctx.createDynamicsCompressor();
            this.compressor.threshold.value = 0.0;
            this.compressor.knee.value = 12;
            this.compressor.ratio.value = 2.0;
            this.compressor.attack.value = 0.003;
            this.compressor.release.value = 0.25;

            // 4. Master Volume Gain (1.0 = unity)
            this.master = ctx.createGain();
            this.master.gain.value = 1.0;

            // 5. Spectrum Analyser for Visualizer
            this.analyser = ctx.createAnalyser();
            this.analyser.fftSize = 128;
            this.analyser.smoothingTimeConstant = 0.75;

            // Connect Graph: source -> filters -> bass -> compressor -> master -> analyser -> destination
            let currentNode = this.source;
            this.filters.forEach((f) => {
                currentNode.connect(f);
                currentNode = f;
            });
            currentNode.connect(this.bass);
            this.bass.connect(this.compressor);
            this.compressor.connect(this.master);
            this.master.connect(this.analyser);
            this.analyser.connect(ctx.destination);

            this.built = true;
            this.startCanvasRender();
        } catch (e) {
            console.warn("VideoFactoryAudioEngine attach notice (direct HTML5 playback active):", e);
        }
    }

    setEQ(gainsInDb) {
        if (!this.ctx || !this.filters.length) return;
        this.resume();
        this.filters.forEach((f, i) => {
            const val = gainsInDb[i] ?? 0;
            f.gain.setTargetAtTime(val, this.ctx.currentTime, 0.03);
        });
    }

    setBassBoost(percentage) {
        if (!this.bass || !this.ctx) return;
        this.resume();
        const dbGain = (Math.max(0, Math.min(100, percentage)) / 100) * 12;
        this.bass.gain.setTargetAtTime(dbGain, this.ctx.currentTime, 0.03);
    }

    setCompressor(enabled) {
        if (!this.compressor || !this.ctx) return;
        this.resume();
        this.compressor.threshold.setTargetAtTime(enabled ? -16 : 0, this.ctx.currentTime, 0.03);
    }

    getSpectrum(numBars = 32) {
        if (!this.analyser) return new Array(numBars).fill(0);
        
        const raw = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(raw);

        const result = [];
        const usableBins = Math.floor(raw.length * 0.82);
        const binsPerBar = Math.max(1, Math.floor(usableBins / numBars));

        for (let i = 0; i < numBars; i++) {
            let sum = 0;
            for (let j = 0; j < binsPerBar; j++) {
                sum += raw[i * binsPerBar + j] || 0;
            }
            const tilt = 1 + (i / numBars) * 0.75;
            const normalizedValue = Math.min(1, (sum / binsPerBar / 255) * tilt);
            result.push(normalizedValue);
        }
        return result;
    }

    startCanvasRender() {
        if (this.animId) cancelAnimationFrame(this.animId);
        const canvas = document.getElementById("lyrics-spectrum-canvas");
        if (!canvas) return;
        const ctx2d = canvas.getContext("2d");
        if (!ctx2d) return;

        const render = () => {
            const width = canvas.offsetWidth || 300;
            const height = canvas.offsetHeight || 60;
            if (canvas.width !== width) canvas.width = width;
            if (canvas.height !== height) canvas.height = height;

            ctx2d.clearRect(0, 0, width, height);

            const numBars = 36;
            const spectrum = this.getSpectrum(numBars);
            const barWidth = (width / numBars) - 2;

            for (let i = 0; i < numBars; i++) {
                const val = Math.max(0.04, spectrum[i]);
                const barHeight = val * height;
                const x = i * (barWidth + 2);
                const y = height - barHeight;

                const grad = ctx2d.createLinearGradient(0, height, 0, 0);
                grad.addColorStop(0, "#FF0000");
                grad.addColorStop(0.5, "#a855f7");
                grad.addColorStop(1, "#06b6d4");

                ctx2d.fillStyle = grad;
                ctx2d.beginPath();
                if (ctx2d.roundRect) {
                    ctx2d.roundRect(x, y, barWidth, barHeight, 3);
                } else {
                    ctx2d.rect(x, y, barWidth, barHeight);
                }
                ctx2d.fill();
            }
            this.animId = requestAnimationFrame(render);
        };
        this.animId = requestAnimationFrame(render);
    }
}

const vfAudioEngine = new VideoFactoryAudioEngine();
window.vfAudioEngine = vfAudioEngine;

function applyEQPreset(presetName) {
    const presets = {
        flat: { gains: [0, 0, 0, 0, 0], bass: 0, comp: false, label: "Pure Direct (Clean)" },
        vocal: { gains: [0, 0, 3, 2, 0], bass: 0, comp: true, label: "Vocal Clarity (+3dB speech)" },
        bass: { gains: [4, 2, 0, 0, 0], bass: 35, comp: false, label: "Bass Boost (+4dB low-end)" },
        sparkle: { gains: [-1, 0, 1, 3, 4], bass: 0, comp: false, label: "Sparkle (+4dB highs)" }
    };
    const p = presets[presetName] || presets.flat;
    vfAudioEngine.currentPreset = presetName;

    vfAudioEngine.setEQ(p.gains);
    vfAudioEngine.setBassBoost(p.bass);
    vfAudioEngine.setCompressor(p.comp);

    const statusLbl = document.getElementById("audio-engine-status-lbl");
    if (statusLbl) statusLbl.textContent = p.label;

    ["flat", "vocal", "bass", "sparkle"].forEach(name => {
        const btn = document.getElementById(`btn-eq-${name}`);
        if (btn) {
            if (name === presetName) {
                btn.style.borderColor = "var(--primary)";
                btn.style.background = "rgba(255, 0, 0, 0.15)";
                btn.style.color = "var(--accent-success)";
                btn.style.fontWeight = "700";
            } else {
                btn.style.borderColor = "";
                btn.style.background = "";
                btn.style.color = "";
                btn.style.fontWeight = "normal";
            }
        }
    });
}
window.applyEQPreset = applyEQPreset;

function formatTimeSec(sec) {
    if (!sec || isNaN(sec)) return "00:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function onAudioMetadataLoaded() {
    const audio = document.getElementById("lyrics-audio-preview");
    const slider = document.getElementById("lyrics-trimmer-slider");
    const durLabel = document.getElementById("trimmer-song-duration");
    if (!audio || !slider) return;

    // Attach Web Audio API Engine
    vfAudioEngine.attach(audio);

    const dur = audio.duration || 0;
    if (durLabel) durLabel.textContent = `Total: ${formatTimeSec(dur)}`;

    slider.max = Math.max(0, Math.floor(dur));
    slider.value = 0;
    onTrimmerSliderChanged();
}
window.onAudioMetadataLoaded = onAudioMetadataLoaded;

function onAudioPlayTriggered() {
    vfAudioEngine.resume();
}
window.onAudioPlayTriggered = onAudioPlayTriggered;

function onAudioPauseTriggered() {
}
window.onAudioPauseTriggered = onAudioPauseTriggered;

function onTrimmerSliderInput() {
    const slider = document.getElementById("lyrics-trimmer-slider");
    const rangeLabel = document.getElementById("trimmer-range-label");
    const clipDurEl = document.getElementById("lyrics-clip-duration");
    const startTimeEl = document.getElementById("lyrics-start-time");

    if (!slider) return;
    const startTime = parseFloat(slider.value || 0);
    const clipDur = clipDurEl ? parseFloat(clipDurEl.value || 30) : 30;
    const endTime = startTime + clipDur;

    if (startTimeEl) startTimeEl.value = Math.floor(startTime);
    if (rangeLabel) rangeLabel.textContent = `${formatTimeSec(startTime)} - ${formatTimeSec(endTime)} (${clipDur.toFixed(1)}s)`;
}
window.onTrimmerSliderInput = onTrimmerSliderInput;

function onTrimmerSliderChanged() {
    const audio = document.getElementById("lyrics-audio-preview");
    const slider = document.getElementById("lyrics-trimmer-slider");
    onTrimmerSliderInput();

    if (audio && slider) {
        const startTime = parseFloat(slider.value || 0);
        vfAudioEngine.resume();
        audio.currentTime = startTime;
    }
}
window.onTrimmerSliderChanged = onTrimmerSliderChanged;

function onAudioTimeUpdated() {
    const audio = document.getElementById("lyrics-audio-preview");
    const slider = document.getElementById("lyrics-trimmer-slider");
    const clipDurEl = document.getElementById("lyrics-clip-duration");
    if (!audio || !slider) return;

    const startTime = parseFloat(slider.value || 0);
    const clipDur = clipDurEl ? parseFloat(clipDurEl.value || 30) : 30;
    const endTime = startTime + clipDur;

    if (audio.currentTime >= endTime) {
        audio.currentTime = startTime;
        audio.pause();
    }
}
window.onAudioTimeUpdated = onAudioTimeUpdated;

function onLyricsSongChanged() {
    const select = document.getElementById("lyrics-song");
    const audio = document.getElementById("lyrics-audio-preview");
    if (!select || !audio) return;

    const opt = select.options[select.selectedIndex];
    const url = opt ? opt.getAttribute("data-url") : null;
    if (url) {
        audio.src = url;
        audio.style.display = "block";
        vfAudioEngine.attach(audio);
    } else {
        audio.style.display = "none";
    }
}
window.onLyricsSongChanged = onLyricsSongChanged;

async function transcribeAndPreviewLyrics() {
    const songSelect = document.getElementById("lyrics-song");
    const btn = document.getElementById("btn-transcribe-preview");
    const customGroup = document.getElementById("group-custom-lyrics");
    const textarea = document.getElementById("lyrics-custom-text");
    const modeSelect = document.getElementById("lyrics-input-mode");
    const langSelect = document.getElementById("lyrics-lang");
    const slider = document.getElementById("lyrics-trimmer-slider");
    const clipDurEl = document.getElementById("lyrics-clip-duration");

    if (!songSelect || !songSelect.value) {
        alert("Please select a song from assets first!");
        return;
    }

    const startTime = slider ? parseFloat(slider.value || 0) : 0.0;
    const clipDuration = clipDurEl ? parseFloat(clipDurEl.value || 30) : 30.0;
    const lang = langSelect ? langSelect.value : "auto";

    const originalHtml = btn ? btn.innerHTML : "";
    if (btn) {
        btn.innerHTML = `<i data-lucide="loader" class="animate-spin"></i> Transcribing 30s Selection (${formatTimeSec(startTime)} - ${formatTimeSec(startTime + clipDuration)})...`;
        btn.disabled = true;
    }

    try {
        const res = await fetch("/api/lyrics/transcribe", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                song_path: songSelect.value,
                language: lang,
                words_per_line: 4,
                start_time: startTime,
                clip_duration: clipDuration,
                audio_mode: "clip"
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Transcription failed");
        }

        const data = await res.json();
        if (textarea && data.lyrics_text) {
            textarea.value = data.lyrics_text;
            if (customGroup) customGroup.style.display = "block";
            if (modeSelect) modeSelect.value = "custom";
            alert(`Lyrics for 30s clip (${formatTimeSec(startTime)} - ${formatTimeSec(startTime + clipDuration)}) transcribed! Review and edit lines below.`);
        } else {
            alert("Whisper AI completed, but no text was generated. You can paste custom lyrics below.");
            if (customGroup) customGroup.style.display = "block";
        }
    } catch(e) {
        alert("Transcription error: " + e.message);
    } finally {
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }
}
window.transcribeAndPreviewLyrics = transcribeAndPreviewLyrics;

let lyricsPollingInterval = null;

async function startLyricsCompilation() {
    let song = document.getElementById("lyrics-song").value;
    let mode = document.getElementById("lyrics-input-mode").value;
    let customLyrics = document.getElementById("lyrics-custom-text").value;
    let niche = document.getElementById("lyrics-niche").value;
    let mood = document.getElementById("lyrics-mood").value;
    let wordsPerLine = document.getElementById("lyrics-words-per-line").value;
    
    let audioModeEl = document.getElementById("lyrics-audio-mode");
    let clipDurationEl = document.getElementById("lyrics-clip-duration");
    let startTimeEl = document.getElementById("lyrics-start-time");
    let aspectRatioEl = document.getElementById("lyrics-aspect-ratio");

    let audioMode = audioModeEl ? audioModeEl.value : "clip";
    let clipDuration = clipDurationEl ? parseFloat(clipDurationEl.value) : 30.0;
    let startTime = startTimeEl ? parseFloat(startTimeEl.value || 0) : 0.0;
    let aspectRatio = aspectRatioEl ? aspectRatioEl.value : "9:16";
    let captionStyleEl = document.getElementById("lyrics-caption-style");
    let captionStyle = captionStyleEl ? captionStyleEl.value : "typing";
    let captionPosEl = document.getElementById("lyrics-caption-position");
    let captionPosition = captionPosEl ? captionPosEl.value : "center";
    let songTitleEl = document.getElementById("lyrics-song-title");
    let songTitle = songTitleEl ? songTitleEl.value : "";
    let includeDanceEl = document.getElementById("lyrics-include-dance");
    let includeDance = includeDanceEl ? includeDanceEl.checked : false;

    if (!song) {
        alert("Please select or upload a song first.");
        return;
    }

    if (mode === "custom" && !customLyrics.trim()) {
        alert("Please paste or transcribe your custom lyrics text first.");
        return;
    }
    
    // Set UI to loading/compiling state
    const progressBar = document.getElementById("lyrics-progress-bar") || document.getElementById("lyrics-overall-progress");
    const statusTxt = document.getElementById("lyrics-overall-status");
    const pctLabel = document.getElementById("lyrics-overall-percent");
    const consoleBox = document.getElementById("lyrics-active-console");
    
    if (statusTxt) statusTxt.textContent = "Compiling: Starting subprocess...";
    if (progressBar) progressBar.style.width = "5%";
    if (pctLabel) pctLabel.textContent = "5%";
    if (consoleBox) consoleBox.textContent = "Initializing Lyric Reel Compiler...\n";
    
    const finishedGallery = document.getElementById("lyrics-finished-gallery");
    const galleryContainer = document.getElementById("lyrics-gallery-container");
    if (finishedGallery) finishedGallery.style.display = "none";
    if (galleryContainer) galleryContainer.innerHTML = "";
    
    try {
        let res = await fetch("/api/lyrics/render", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                song_path: song,
                mode: mode,
                custom_lyrics: customLyrics,
                niche: niche,
                mood: mood,
                words_per_line: parseInt(wordsPerLine),
                language: "english",
                audio_mode: audioMode,
                clip_duration: clipDuration,
                start_time: startTime,
                aspect_ratio: aspectRatio,
                caption_style: captionStyle,
                caption_position: captionPosition,
                song_title: songTitle,
                include_dance: includeDance
            })
        });
        
        if (!res.ok) {
            let err = await res.json();
            throw new Error(err.detail || "Lyrics compile start failed");
        }
        
        // Start polling status
        if (lyricsPollingInterval) clearInterval(lyricsPollingInterval);
        
        let checkProgress = async () => {
            try {
                let statusRes = await fetch("/api/render/status");
                let statusData = await statusRes.json();
                
                const currentConsole = document.getElementById("lyrics-active-console");
                if (currentConsole && statusData.log) {
                    currentConsole.textContent = statusData.log;
                    currentConsole.scrollTop = currentConsole.scrollHeight;
                }
                
                const curStatusTxt = document.getElementById("lyrics-overall-status");
                const curPctLabel = document.getElementById("lyrics-overall-percent");
                const curProgressBar = document.getElementById("lyrics-progress-bar") || document.getElementById("lyrics-overall-progress");
                
                if (curStatusTxt) curStatusTxt.textContent = statusData.step_label || "Compiling...";
                if (curProgressBar) curProgressBar.style.width = `${statusData.progress}%`;
                if (curPctLabel) curPctLabel.textContent = `${statusData.progress}%`;
                
                if (statusData.status === "completed") {
                    clearInterval(lyricsPollingInterval);
                    if (curStatusTxt) curStatusTxt.textContent = "Completed Successfully!";
                    
                    let videoUrl = `/output/videos/${statusData.output_file}`;
                    if (finishedGallery) finishedGallery.style.display = "block";
                    if (galleryContainer) {
                        galleryContainer.innerHTML = `
                            <div class="phone-mockup" style="width: 240px; height: 426px; border-width: 8px; border-radius: 24px; margin-top: 1rem;">
                                <div class="phone-notch" style="width: 80px; height: 12px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;"></div>
                                <video class="phone-screen" src="${videoUrl}" controls autoplay loop style="object-fit: cover;"></video>
                            </div>
                        `;
                    }
                    console.log("Lyric Reel compiled successfully!");
                } else if (statusData.status === "failed") {
                    clearInterval(lyricsPollingInterval);
                    if (curStatusTxt) curStatusTxt.textContent = "Failed!";
                }
            } catch (pollErr) {
                console.error(pollErr);
                clearInterval(lyricsPollingInterval);
            }
        };
        
        lyricsPollingInterval = setInterval(checkProgress, 750);
        
    } catch (err) {
        console.error(err);
        alert("Failed to start lyrics compilation: " + err.message);
    }
}
window.startLyricsCompilation = startLyricsCompilation;
window.downloadRenderedVideo = downloadRenderedVideo;
window.copyRenderedVideoPath = copyRenderedVideoPath;
window.openFullscreenPreview = openFullscreenPreview;

/* ================================================================
   VOICE LAB (TTS Studio) CONTROLLER
================================================================ */
let vlabAllVoices = [];
let vlabCurrentAudioUrl = null;
let vlabSelectedVoice = null;

async function vlabLoadVoices(forceRefresh = false) {
    const loadingEl = document.getElementById("vlab-loading");
    const gridEl = document.getElementById("vlab-grid");
    const countEl = document.getElementById("vlab-count");
    const emptyEl = document.getElementById("vlab-empty");

    if (loadingEl) loadingEl.style.display = "block";
    if (gridEl) gridEl.style.display = "none";
    if (emptyEl) emptyEl.style.display = "none";
    if (countEl) countEl.textContent = "Loading...";

    try {
        const res = await fetch(`/api/tts/voices${forceRefresh ? '?force_refresh=true' : ''}`);
        const data = await res.json();
        vlabAllVoices = data.voices || [];
        vlabFilterVoices();
    } catch (err) {
        console.error("Failed to load voices:", err);
        if (loadingEl) loadingEl.innerHTML = `<p style="color:var(--accent-error);">Failed to load voices: ${err.message}</p>`;
    }
}

function vlabFilterVoices() {
    const langVal = document.getElementById("vlab-lang")?.value || "";
    const provVal = document.getElementById("vlab-provider")?.value || "";
    const genderVal = document.getElementById("vlab-gender")?.value || "";

    const loadingEl = document.getElementById("vlab-loading");
    const gridEl = document.getElementById("vlab-grid");
    const countEl = document.getElementById("vlab-count");
    const emptyEl = document.getElementById("vlab-empty");

    if (loadingEl) loadingEl.style.display = "none";

    let filtered = vlabAllVoices.filter(v => {
        // Exclude robotic Daudi and Rehema
        if (v.voice_id.includes("Daudi") || v.voice_id.includes("Rehema")) return false;
        if (langVal && v.lang_code !== langVal) return false;
        if (provVal && v.provider !== provVal) return false;
        if (genderVal && v.gender !== genderVal) return false;
        return true;
    });

    if (countEl) countEl.textContent = `${filtered.length} Voices`;

    if (!filtered.length) {
        if (gridEl) gridEl.style.display = "none";
        if (emptyEl) emptyEl.style.display = "block";
        return;
    }

    if (emptyEl) emptyEl.style.display = "none";
    if (gridEl) {
        gridEl.style.display = "grid";
        gridEl.innerHTML = filtered.map(v => {
            let provBadge = "badge-edge";
            let provLabel = "EDGE TTS";
            let badgeColor = "var(--primary)";
            let badgeBg = "rgba(14,165,233,0.12)";

            if (v.provider === "direct-gemini") {
                provBadge = "badge-gemini";
                provLabel = "GEMINI AI";
                badgeColor = "#38bdf8";
                badgeBg = "rgba(56,189,248,0.15)";
            } else if (v.provider === "elevenlabs") {
                provBadge = "badge-elevenlabs";
                provLabel = "ELEVENLABS";
                badgeColor = "#34d399";
                badgeBg = "rgba(16,185,129,0.15)";
            } else if (v.provider === "puter") {
                provBadge = "badge-puter";
                provLabel = "PUTER AI";
                badgeColor = "#f59e0b";
                badgeBg = "rgba(245,158,11,0.15)";
            }

            return `
                <div class="voice-card ${provBadge}" style="background: rgba(15, 23, 42, 0.65); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.1rem; display: flex; flex-direction: column; justify-content: space-between; gap: 0.75rem; transition: transform 0.2s, border-color 0.2s;">
                    <div>
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem;">
                            <span style="font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: ${badgeColor}; background: ${badgeBg}; padding: 0.2rem 0.5rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">${provLabel}</span>
                            <span style="font-size: 0.75rem; color: var(--text-muted);">${v.gender || 'Neural'}</span>
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-main); line-height: 1.3;">${v.display_name.replace(/\[.*?\]\s*/g, '')}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">ID: <code style="font-family:var(--font-code); font-size:0.7rem; color:#93c5fd;">${v.voice_id}</code></div>
                    </div>
                    <button class="btn btn-secondary" onclick="vlabPreviewVoice('${v.voice_id}', '${v.provider}')" style="width: 100%; padding: 0.55rem; font-size: 0.82rem; border-radius: 8px;">
                        <i data-lucide="play" style="width:14px; height:14px;"></i> Listen Preview
                    </button>
                </div>
            `;
        }).join("");
        if (typeof lucide !== "undefined") lucide.createIcons();
    }
}

async function vlabPreviewVoice(voiceId, provider) {
    const text = document.getElementById("vlab-preview-text")?.value || "Mungu hakusahau. Amini Yeye leo.";
    const playerSection = document.getElementById("vlab-player-section");
    const playingVoice = document.getElementById("vlab-playing-voice");
    const audioEl = document.getElementById("vlab-audio");
    const useBtn = document.getElementById("vlab-use-btn");

    if (playingVoice) playingVoice.textContent = `${voiceId} (${provider})`;
    if (playerSection) playerSection.style.display = "block";

    try {
        if (playingVoice) playingVoice.innerHTML = `${voiceId} <i data-lucide="loader" class="animate-spin" style="width:14px; height:14px; display:inline-block;"></i>`;
        if (typeof lucide !== "undefined") lucide.createIcons();

        const res = await fetch("/api/tts/preview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ voice: voiceId, text: text, rate: "+0%" })
        });
        const data = await res.json();
        if (data.audio_url) {
            vlabCurrentAudioUrl = data.audio_url;
            vlabSelectedVoice = { voice: voiceId, provider: provider };
            if (audioEl) {
                audioEl.src = data.audio_url;
                audioEl.play();
            }
            if (playingVoice) playingVoice.textContent = `${voiceId} (${provider})`;
            if (useBtn) useBtn.style.display = "inline-flex";
        } else {
            alert("Preview error: " + (data.error || "Could not generate audio"));
        }
    } catch (e) {
        alert("Failed to generate preview: " + e.message);
    }
}

async function vlabUseThisVoice() {
    if (!vlabSelectedVoice) return;
    try {
        const provSelect = document.getElementById("settings-tts-provider");
        if (provSelect) {
            provSelect.value = vlabSelectedVoice.provider;
            updateSettingsVoiceDropdown(vlabSelectedVoice.voice);
        }
        await saveSystemSettings();
        alert(`Active voice set to: ${vlabSelectedVoice.voice}!`);
    } catch (e) {
        alert("Failed to set voice: " + e.message);
    }
}

window.vlabLoadVoices = vlabLoadVoices;
window.vlabFilterVoices = vlabFilterVoices;
window.vlabPreviewVoice = vlabPreviewVoice;
window.vlabUseThisVoice = vlabUseThisVoice;

// ================================================================
// LONGFORM CLIPPER — sermons/podcasts → captioned vertical shorts
// ================================================================
let clipperPollInterval = null;
let clipperActiveJob = null;
let clipperLastCandidates = [];

function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function setClipperConsole(text) {
    const box = document.getElementById('clipper-console');
    if (!box) return;
    box.textContent = text;
    box.scrollTop = box.scrollHeight;
}

function clipperErrorText(data, fallback) {
    const d = data && data.detail;
    if (typeof d === 'string' && d) return d;
    if (d) { try { return JSON.stringify(d); } catch (e) { /* ignore */ } }
    return fallback;
}

async function loadClipperSources() {
    const sel = document.getElementById('clipper-source');
    if (!sel) return;
    try {
        const res = await fetch('/api/clipper/sources');
        const data = await res.json();
        if (!res.ok) throw new Error(clipperErrorText(data, 'failed to load sources'));
        const prev = sel.value;
        sel.innerHTML = '';
        const sources = data.sources || [];
        if (!sources.length) {
            sel.innerHTML = '<option value="">— No videos in assets/longform yet —</option>';
            setClipperConsole('No source videos found. Upload one below, or drop files into assets/longform/.');
            return;
        }
        for (const s of sources) {
            const opt = document.createElement('option');
            opt.value = s.name;
            const dur = s.duration ? formatTimeSec(Math.floor(s.duration)) : '--:--';
            const mark = s.analyzed ? '  ·  ✓ analyzed' : '';
            opt.textContent = `${s.name}  ·  ${dur}${mark}`;
            sel.appendChild(opt);
        }
        if (prev && Array.from(sel.options).some(o => o.value === prev)) {
            sel.value = prev;
        }
    } catch (e) {
        setClipperConsole('⚠ Failed to load sources: ' + e.message);
    }
}

async function uploadClipperVideo() {
    const input = document.getElementById('clipper-upload-file');
    const status = document.getElementById('clipper-upload-status');
    if (!input || !input.files || !input.files.length) return;

    const fd = new FormData();
    fd.append('file', input.files[0]);
    if (status) status.textContent = 'Uploading…';
    setClipperConsole(`Uploading ${input.files[0].name} ...`);

    try {
        const res = await fetch('/api/clipper/upload', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(clipperErrorText(data, 'upload failed'));
        if (status) status.textContent = '✓ Uploaded';
        input.value = '';
        await loadClipperSources();
        const sel = document.getElementById('clipper-source');
        if (sel && data.name) sel.value = data.name;
        setClipperConsole(`✅ Uploaded ${data.name} (${data.size_mb} MB) — ready to analyze.`);
    } catch (e) {
        if (status) status.textContent = '✗ Failed';
        setClipperConsole('⚠ Upload failed: ' + e.message);
    }
}

function clipperReadParams() {
    const g = id => document.getElementById(id);
    const sourceSel = g('clipper-source');
    const source = sourceSel ? sourceSel.value : '';
    if (!source) {
        alert('Choose or upload a source video first.');
        return null;
    }
    const minDur = parseFloat((g('clipper-min') || {}).value || '20');
    const maxDur = parseFloat((g('clipper-max') || {}).value || '50');
    if (!(maxDur > minDur)) {
        alert('Max length must be greater than min length.');
        return null;
    }
    return {
        source,
        language: (g('clipper-language') || {}).value || 'auto',
        model: (g('clipper-model') || {}).value || 'base',
        min_dur: minDur,
        max_dur: maxDur,
        count: parseInt((g('clipper-count') || {}).value || '3', 10) || 3,
        words_per_line: parseInt((g('clipper-words') || {}).value || '4', 10) || 4,
        crop: (g('clipper-crop') || {}).value || 'center',
        niche: (g('clipper-niche') || {}).value || 'gospel',
        mood: (g('clipper-mood') || {}).value || 'peaceful',
    };
}

function clipperSetBusy(busy) {
    ['clipper-analyze-btn', 'clipper-render-btn'].forEach(id => {
        const b = document.getElementById(id);
        if (b) b.disabled = !!busy;
    });
}

function clipperResetPanel(prefix) {
    const panel = document.getElementById(prefix + '-panel');
    if (panel) panel.style.display = 'block';
    const st = document.getElementById(prefix + '-status');
    if (st) st.textContent = 'RUNNING';
    const pc = document.getElementById(prefix + '-pct');
    if (pc) pc.textContent = '0%';
    const bar = document.getElementById(prefix + '-bar');
    if (bar) bar.style.width = '0%';
}

function clipperUpdatePanel(prefix, status, pct) {
    const panel = document.getElementById(prefix + '-panel');
    if (panel) panel.style.display = 'block';
    const st = document.getElementById(prefix + '-status');
    if (st) st.textContent = String(status || '').toUpperCase();
    const pc = document.getElementById(prefix + '-pct');
    if (pc) pc.textContent = `${pct}%`;
    const bar = document.getElementById(prefix + '-bar');
    if (bar) bar.style.width = `${pct}%`;
}

async function startClipperAnalyze() {
    const params = clipperReadParams();
    if (!params) return;

    clipperResetPanel('clipper-analyze');
    clipperSetBusy(true);

    try {
        const res = await fetch('/api/clipper/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(clipperErrorText(data, 'failed to start analysis'));
        setClipperConsole('🔍 Analysis started — extracting audio & transcribing with Whisper...\n');
        beginClipperPoll('analyze');
    } catch (e) {
        clipperSetBusy(false);
        const panel = document.getElementById('clipper-analyze-panel');
        if (panel) panel.style.display = 'none';
        setClipperConsole('⚠ ' + e.message);
    }
}

async function renderClipperClips() {
    const params = clipperReadParams();
    if (!params) return;

    // Send exact time windows (not ranks): re-scoring between analyze and
    // render must never change WHICH moment gets clipped.
    const checkedRanks = Array.from(document.querySelectorAll('input[name="clipper-cand"]:checked'))
        .map(el => parseInt(el.value, 10))
        .filter(n => !isNaN(n));
    if (checkedRanks.length) {
        const byRank = new Map(clipperLastCandidates.map(c => [Number(c.rank), c]));
        params.selected = checkedRanks
            .map(r => {
                const c = byRank.get(r);
                return c ? { start: Number(c.start), end: Number(c.end) } : null;
            })
            .filter(Boolean);
        if (!params.selected.length) {
            alert('Candidate details missing — run Analyze again, then render.');
            return;
        }
    } else {
        params.selected = null;
    }

    clipperResetPanel('clipper-render');
    clipperSetBusy(true);

    try {
        const res = await fetch('/api/clipper/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(clipperErrorText(data, 'failed to start render'));
        const how = params.selected
            ? `${params.selected.length} selected clip(s)`
            : `top ${params.count} candidates`;
        setClipperConsole(`🎬 Render started (${how}) — analyzing (cached) + encoding...\n`);
        beginClipperPoll('render');
    } catch (e) {
        clipperSetBusy(false);
        const panel = document.getElementById('clipper-render-panel');
        if (panel) panel.style.display = 'none';
        setClipperConsole('⚠ ' + e.message);
    }
}

function beginClipperPoll(job) {
    clipperActiveJob = job;
    if (clipperPollInterval) clearInterval(clipperPollInterval);
    pollClipperStatus();
    clipperPollInterval = setInterval(pollClipperStatus, 800);
}

async function pollClipperStatus() {
    let d;
    try {
        const res = await fetch('/api/clipper/status');
        d = await res.json();
        if (!res.ok) throw new Error(clipperErrorText(d, 'status request failed'));
    } catch (e) {
        // transient fetch failure — keep polling; a dead job is detected server-side
        return;
    }

    const job = d.job || clipperActiveJob || 'analyze';
    const prefix = job === 'render' ? 'clipper-render' : 'clipper-analyze';
    clipperUpdatePanel(prefix, d.status, d.progress || 0);

    const box = document.getElementById('clipper-console');
    if (box) {
        let text = d.log || '';
        if (d.status === 'failed' && d.error) text += `\n❌ ${d.error}`;
        if (text) {
            box.textContent = text;
            box.scrollTop = box.scrollHeight;
        }
    }

    if (d.status === 'running') return;

    if (clipperPollInterval) clearInterval(clipperPollInterval);
    clipperPollInterval = null;
    clipperSetBusy(false);

    if (d.status === 'completed') {
        if (Array.isArray(d.candidates) && d.candidates.length) {
            renderClipperCandidates(d.candidates);
        }
        if (job === 'render') {
            showClipperOutputs(Array.isArray(d.outputs) ? d.outputs : []);
        }
        if (job === 'analyze') {
            const cands = document.getElementById('clipper-candidates');
            if (cands) cands.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    } else if (d.status === 'failed') {
        const panel = document.getElementById(prefix + '-status');
        if (panel) panel.textContent = 'FAILED';
    }
}

function renderClipperCandidates(list) {
    const box = document.getElementById('clipper-candidates');
    const countEl = document.getElementById('clipper-candidate-count');
    if (!box) return;
    clipperLastCandidates = Array.isArray(list) ? list : [];

    if (!Array.isArray(list) || !list.length) {
        box.innerHTML = '<div style="font-size: 0.85rem; color: var(--text-muted); padding: 1.25rem; border: 1px dashed var(--border-subtle); border-radius: 10px; text-align: center;">' +
            'No candidates found — try a longer source, another language, or smaller min length.</div>';
        if (countEl) countEl.textContent = '';
        return;
    }

    const topN = Math.max(1, parseInt((document.getElementById('clipper-count') || {}).value || '3', 10) || 3);

    box.innerHTML = list.map((c, i) => {
        const start = Number(c.start) || 0;
        const end = Number(c.end) || 0;
        const dur = Number(c.duration) || (end - start);
        const score = Number(c.score) || 0;
        const rank = Number(c.rank) || (i + 1);

        const badges = [];
        if (c.hooks) badges.push(`🪝 ${c.hooks} hook ${c.hooks === 1 ? 'word' : 'words'}`);
        if (c.question) badges.push('❓ question');
        if (c.number) badges.push('🔢 number');
        if (c.wps) badges.push(`⚡ ${Math.round(Number(c.wps))} w/s`);

        const badgeHtml = badges.length
            ? `<div style="margin-top: 0.4rem; display: flex; gap: 0.4rem; flex-wrap: wrap;">` +
              badges.map(b => `<span style="font-size: 0.7rem; padding: 0.15rem 0.5rem; background: rgba(255,255,255,0.05); border: 1px solid var(--border-subtle); border-radius: 99px; color: var(--text-muted);">${b}</span>`).join('') +
              `</div>`
            : '';

        return `
        <div class="glass-card" style="padding: 0.7rem 0.9rem; margin-bottom: 0.55rem; border-radius: 10px; display: flex; gap: 0.7rem; align-items: flex-start; background: rgba(255,255,255,0.02);">
            <input type="checkbox" name="clipper-cand" value="${rank}" ${i < topN ? 'checked' : ''} onchange="onClipperCandidateToggle()" style="margin-top: 0.35rem; accent-color: var(--primary); width: 16px; height: 16px; cursor: pointer; flex-shrink: 0;">
            <div style="flex: 1; min-width: 0;">
                <div style="display: flex; justify-content: space-between; gap: 0.5rem; font-size: 0.76rem; color: var(--text-muted); font-family: var(--font-code);">
                    <span>#${rank} · ${formatTimeSec(Math.floor(start))} → ${formatTimeSec(Math.floor(end))} · ${dur.toFixed(1)}s</span>
                    <span style="color: var(--primary); font-weight: 700; white-space: nowrap;">★ ${score.toFixed(1)}</span>
                </div>
                <div style="font-size: 0.9rem; margin-top: 0.35rem; color: var(--text-main); line-height: 1.5; word-break: break-word;">${escapeHtml(c.text)}</div>
                ${badgeHtml}
            </div>
        </div>`;
    }).join('');

    if (countEl) countEl.textContent = `(${list.length} found)`;
    onClipperCandidateToggle();
    if (window.lucide) lucide.createIcons();
}

function onClipperCandidateToggle() {
    const countEl = document.getElementById('clipper-candidate-count');
    if (!countEl) return;
    const all = document.querySelectorAll('input[name="clipper-cand"]').length;
    if (!all) return;
    const checked = document.querySelectorAll('input[name="clipper-cand"]:checked').length;
    countEl.textContent = `(${all} found · ${checked} selected)`;
}

function showClipperOutputs(list) {
    const box = document.getElementById('clipper-output-list');
    if (!box) return;

    if (!Array.isArray(list) || !list.length) {
        box.innerHTML = '<div style="font-size: 0.85rem; color: var(--text-muted); padding: 1.25rem; border: 1px dashed var(--border-subtle); border-radius: 10px; text-align: center;">No clips rendered yet.</div>';
        return;
    }

    box.innerHTML = list.map(o => {
        const url = encodeURI(o.url || '');
        const kitUrl = o.social_kit_url ? encodeURI(o.social_kit_url) : '';
        const title = escapeHtml(o.title || o.name || 'Clip');
        const dur = Number(o.duration) || 0;
        const size = Number(o.size_mb) || 0;
        return `
        <div class="glass-card" style="padding: 0.8rem; margin-bottom: 0.75rem; border-radius: 12px; background: rgba(255,255,255,0.02);">
            <video src="${url}" controls preload="metadata" playsinline style="width: 100%; max-height: 320px; border-radius: 10px; background: #000; display: block;"></video>
            <div style="display: flex; justify-content: space-between; gap: 0.5rem; margin-top: 0.55rem; font-size: 0.8rem; color: var(--text-muted);">
                <span style="color: var(--text-main); font-weight: 600; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${title}">${title}</span>
                <span style="white-space: nowrap;">${dur}s · ${size} MB</span>
            </div>
            <div style="display: flex; gap: 0.5rem; margin-top: 0.65rem; flex-wrap: wrap;">
                <a class="btn btn-secondary" href="${url}" download style="padding: 0.35rem 0.75rem; font-size: 0.75rem; height: auto; border-radius: 6px;">⬇ MP4</a>
                ${kitUrl ? `<a class="btn btn-secondary" href="${kitUrl}" target="_blank" rel="noopener" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; height: auto; border-radius: 6px;">#️⃣ Caption Kit</a>` : ''}
                <button class="btn btn-secondary" onclick="scheduleClipperClip('${escapeHtml(o.name || '').replace(/'/g, '&#39;')}')" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; height: auto; border-radius: 6px;">📅 Schedule</button>
            </div>
        </div>`;
    }).join('');

    if (window.lucide) lucide.createIcons();
    const scroller = document.getElementById('clipper-outputs');
    if (scroller) scroller.scrollTop = 0;
}

function scheduleClipperClip(videoName) {
    if (!videoName) return;
    switchTab('scheduler');
    setTimeout(async () => {
        if (typeof setQueueVideoMode === 'function') setQueueVideoMode('rendered');
        if (typeof loadRenderedVideoList === 'function') {
            try { await loadRenderedVideoList(); } catch (e) { /* list refresh is best-effort */ }
        }
        const sel = document.getElementById('queue-rendered-video');
        if (sel) {
            const match = Array.from(sel.options).find(o => o.value === videoName);
            if (match) sel.value = videoName;
        }
    }, 250);
}

window.loadClipperSources = loadClipperSources;
window.uploadClipperVideo = uploadClipperVideo;
window.startClipperAnalyze = startClipperAnalyze;
window.renderClipperClips = renderClipperClips;
window.pollClipperStatus = pollClipperStatus;
window.renderClipperCandidates = renderClipperCandidates;
window.showClipperOutputs = showClipperOutputs;
window.onClipperCandidateToggle = onClipperCandidateToggle;
window.scheduleClipperClip = scheduleClipperClip;
window.escapeHtml = escapeHtml;


