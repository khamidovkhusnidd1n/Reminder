/**
 * MEng APro - Logic (Premium Edition)
 */

let units = [];
let currentUnitWords = [];
let currentUnitName = "";
let customUnits = JSON.parse(localStorage.getItem('my_custom_units')) || [];
let currentIndex = 0;
let score = 0;
let combo = 0;
let autoNextTimer;

// Stats Persistence
let stats = JSON.parse(localStorage.getItem('me_stats')) || {
    xp: 0,
    level: 1,
    streak: 0,
    nickname: "",
    lastDate: null,
    masteredUnits: {}
};

function saveStats() {
    localStorage.setItem('me_stats', JSON.stringify(stats));
    updateStatsUI();
}

function addXP(amount) {
    const gain = amount + (combo * 2);
    stats.xp += gain;

    const nextLevelXP = stats.level * 120; // Slightly harder levels
    if (stats.xp >= nextLevelXP) {
        stats.level++;
        stats.xp = 0;
        showLevelUp();
    }
    saveStats();
    return gain;
}

// HUD & Navbar UI Helpers
function updateNavActive(el) {
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    el.classList.add('active');
}

// --- Online Leaderboard (Pantry Cloud) ---
// 1. https://getpantry.cloud saytiga kiring "Get Started" bosing.
// 2. Yangi Pantry yarating.
// 3. O'sha Pantry ID raqamini shu yerga yozing:
const YOUR_PANTRY_ID = "af7d8502-edc4-4cc1-9cfc-aff8824f08e0"; // Masalan: "8472-3232-..."
const BUCKET_NAME = "ReminderLeaderboard";

async function updateRanksXP() {
    const list = document.getElementById('ranks-list');
    if (!list) return;

    // 1. Show Local State First (Immediate Feedback)
    const totalXP = (stats.level * 120) + stats.xp;
    const myName = stats.nickname || "YOU";

    // Agar ID qo'yilmagan bo'lsa, faqat o'zini ko'rsatadi
    if (!YOUR_PANTRY_ID) {
        list.innerHTML = `
            <div style="background:rgba(255,165,0,0.1); border:1px solid orange; padding:10px; border-radius:12px; margin-bottom:12px;">
                <p style="font-size:0.75rem; color:orange;">⚠️ Onlayn rejim ishlashi uchun <b>app.js</b> fayliga <b>Pantry ID</b> kiritishingiz kerak.</p>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,215,0,0.1); border:1px solid gold; padding:16px; border-radius:16px;">
                <span style="font-weight:800;">${myName}</span>
                <span style="color:gold; font-weight:800;">${totalXP} XP</span>
            </div>
        `;
        return;
    }

    list.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted);">Yuklanmoqda...</div>`;

    try {
        const url = `https://getpantry.cloud/apiv1/pantry/${YOUR_PANTRY_ID}/basket/${BUCKET_NAME}`;

        // 2. Fetch remote data
        let players = [];
        try {
            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                players = data.players || [];
            }
        } catch (e) {
            console.log("Creating new leaderboard...");
        }

        // 3. Update/Add Self
        // Remove old version of myself (by name)
        players = players.filter(p => p.name !== myName);

        // Add current state
        players.push({
            name: myName,
            xp: totalXP,
            lastSeen: Date.now()
        });

        // 4. Sort & Limit
        players.sort((a, b) => b.xp - a.xp);
        players = players.slice(0, 50); // Keep top 50 only

        // 5. Send back to cloud (Background sync)
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ players: players })
        }).catch(err => console.error("Save error:", err));

        // 6. Render Full List
        list.innerHTML = '';
        players.forEach((u, i) => {
            const isMe = u.name === myName;
            const item = document.createElement('div');

            const bg = isMe ? 'rgba(255,215,0,0.15)' : 'rgba(255,255,255,0.05)';
            const border = isMe ? '1px solid gold' : '1px solid var(--glass-border)';
            const color = isMe ? 'gold' : '#fff';
            const rankDisplay = i < 3 ? ['🥇', '🥈', '🥉'][i] : `#${i + 1}`;

            item.style = `display:flex; justify-content:space-between; align-items:center; background:${bg}; border:${border}; padding:14px; border-radius:14px; margin-bottom:8px;`;
            if (isMe) item.style.transform = "scale(1.02)";

            item.innerHTML = `
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.2rem; min-width:24px; font-weight:800;">${rankDisplay}</span>
                    <div>
                        <span style="font-weight:${isMe ? '900' : '700'}; color:${color}; font-size:0.95rem; display:block;">${u.name}</span>
                        <span style="font-size:0.65rem; color:var(--text-muted);">${isMe ? 'online' : 'player'}</span>
                    </div>
                </div>
                <span style="font-weight:800; color:var(--accent);">${u.xp} XP</span>
            `;
            list.appendChild(item);
        });

    } catch (err) {
        console.error(err);
        list.innerHTML = `<div style="color:var(--error); text-align:center;">Internet xatosi!</div>`;
    }
}

// Text-to-Speech Helper
function speak(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop previous
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'en-US';
        msg.rate = 0.9; // Slightly slower for clarity
        msg.pitch = 1;
        window.speechSynthesis.speak(msg);
    }
}

function updateStatsUI() {
    // HUD Circle Progress
    const circle = document.getElementById('user-level-circle');
    const lvlText = document.getElementById('user-level');
    const streakPill = document.getElementById('user-streak');

    if (circle) {
        const nextLevelXP = stats.level * 120;
        const progress = (stats.xp / nextLevelXP) * 100;
        circle.style.setProperty('--progress', `${progress}%`);
        circle.setAttribute('data-level', stats.level);
    }
    if (lvlText) lvlText.innerText = `LEVEL ${stats.level}`;
    if (streakPill) streakPill.innerText = `🔥 ${stats.streak}`;
    updateRanksXP(); // Sync nickname to ranks
}

function spawnXP(amount) {
    const el = document.createElement('div');
    el.className = 'xp-tag';

    // Random encouraging Uzbek word
    const phrases = ['BARAKALLA!', 'O\'XSHADI!', 'SUPER!', 'DAVOM ET!', 'AJOYIB!'];
    const phrase = phrases[Math.floor(Math.random() * phrases.length)];

    el.innerHTML = `<span style="display:block; font-size:0.7rem; opacity:0.7;">+${amount} XP</span>${phrase}`;

    // Center of screen/word area
    el.style.left = '50%';
    el.style.top = '40%';
    el.style.transform = 'translate(-50%, -50%)';

    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1200);
}

// --- Navigation ---
const screens = ['onboarding', 'units', 'modes', 'flashcard', 'game', 'test', 'results', 'manage', 'ranks', 'settings', 'parts'];
function showScreen(target) {
    // Hide all screens
    screens.forEach(s => {
        const el = document.getElementById(`screen-${s}`);
        if (el) el.classList.add('hidden');
    });

    // Show target
    const targetEl = document.getElementById(`screen-${target}`);
    if (targetEl) targetEl.classList.remove('hidden');

    // Manage Global UI (Header, Navbar, Global HUD)
    // Only show these on "Main Dashboard" screens
    const mainScreens = ['units', 'manage', 'ranks', 'settings'];
    const showGlobal = mainScreens.includes(target);

    const header = document.querySelector('header');
    const globalHud = document.getElementById('global-hud');
    const navbar = document.querySelector('.navbar');

    if (showGlobal) {
        if (header) header.classList.remove('hidden');
        if (globalHud) globalHud.classList.remove('hidden');
        if (navbar) navbar.classList.remove('hidden');
    } else {
        if (header) header.classList.add('hidden');
        if (globalHud) globalHud.classList.add('hidden');
        if (navbar) navbar.classList.add('hidden');
    }

    updateNavActive(document.querySelector(`.nav-item[onclick*="'${target}'"]`) || document.getElementById('nav-home'));
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// --- Data Parsing ---
function parseWords() {
    units = [];
    if (typeof RAW_DATA === 'undefined') return;
    const lines = RAW_DATA.split('\n');
    let currentUnit = null;

    lines.forEach(line => {
        const trimmed = line.trim();
        if (!trimmed) return;
        if (trimmed.startsWith('Unit')) {
            currentUnit = { name: trimmed, words: [] };
            units.push(currentUnit);
        } else if (currentUnit && (trimmed.includes('–') || trimmed.includes('-'))) {
            const sep = trimmed.includes('–') ? '–' : '-';
            const parts = trimmed.split(sep);
            const english = parts[0].replace(/\(.*?\)/, '').trim();
            const typeMatch = parts[0].match(/\((.*?)\)/);
            const type = typeMatch ? typeMatch[1] : 'word';
            currentUnit.words.push({ english, uzbek: parts[1].trim(), type });
        }
    });

    customUnits.forEach(u => {
        units.push({ ...u, isCustom: true });
    });
}

// --- UI Components ---
function renderUnits() {
    const list = document.getElementById('unit-list');
    if (!list) return;
    list.innerHTML = '';

    units.forEach((unit, i) => {
        const card = document.createElement('div');
        card.className = 'unit-card fade-up';
        card.style.animationDelay = `${i * 0.08}s`;
        // Check Mastery
        let badge = '';
        if (unit.words.length > 30) {
            // Check parts mastery
            const chunkSize = 25;
            const partsCount = Math.ceil(unit.words.length / chunkSize);
            let masteredCount = 0;
            for (let p = 1; p <= partsCount; p++) {
                if (stats.masteredUnits[`${unit.name} (Part ${p})`]) masteredCount++;
            }
            if (masteredCount === partsCount) badge = '<span class="mastered-badge">✅</span>';
            else if (masteredCount > 0) badge = `<span class="mastered-badge" style="font-size:0.7rem; color:var(--accent);">${masteredCount}/${partsCount}</span>`;
        } else {
            if (stats.masteredUnits[unit.name]) badge = '<span class="mastered-badge">✅</span>';
        }

        card.innerHTML = `
            <div class="unit-info">
                <span class="meta">${unit.isCustom ? 'User Data' : 'OUP Source'} • ${unit.words.length} Words</span>
                <span class="name">${unit.name} ${badge}</span>
            </div>
            <div class="unit-arrow">→</div>
        `;
        card.onclick = () => {
            // Split logic
            if (unit.words.length > 30) {
                renderParts(unit);
                showScreen('parts');
            } else {
                currentUnitWords = [...unit.words];
                currentUnitName = unit.name;
                document.getElementById('selected-unit-name').innerText = unit.name;
                document.getElementById('selected-unit-count').innerText = `${unit.words.length} Vocabulary Items`;
                showScreen('modes');
            }
        };
        list.appendChild(card);
    });
}

function renderParts(unit) {
    const list = document.getElementById('parts-list');
    document.getElementById('parts-unit-name').innerText = unit.name;
    list.innerHTML = '';

    // Chunk size 25
    const chunkSize = 25;
    const partsCount = Math.ceil(unit.words.length / chunkSize);

    for (let i = 0; i < partsCount; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, unit.words.length);
        const partWords = unit.words.slice(start, end);

        const partName = `${unit.name} (Part ${i + 1})`;

        const card = document.createElement('div');
        card.className = 'unit-card fade-up';
        card.style.animationDelay = `${i * 0.1}s`;
        card.innerHTML = `
            <div class="unit-info">
                <span class="meta">${start + 1} - ${end}</span>
                <span class="name">Part ${i + 1} ${stats.masteredUnits[partName] ? '<span class="mastered-badge">✅</span>' : ''}</span>
            </div>
            <div class="unit-arrow">→</div>
        `;

        card.onclick = () => {
            currentUnitWords = [...partWords];
            currentUnitName = partName;
            document.getElementById('selected-unit-name').innerText = currentUnitName;
            document.getElementById('selected-unit-count').innerText = `${partWords.length} Words`;

            // Adjust back button on modes screen to go back to parts
            const backBtn = document.getElementById('back-to-units');
            backBtn.innerText = "← BACK TO PARTS";
            backBtn.onclick = () => showScreen('parts');

            showScreen('modes');
        };
        list.appendChild(card);
    }
}

// --- Mode Logic ---
function nextCard() {
    clearTimeout(autoNextTimer);
    if (currentIndex < currentUnitWords.length - 1) {
        currentIndex++;
        updateFlashcard();
    } else finishMode();
}

function updateFlashcard() {
    addXP(2); // View bonus
    const word = currentUnitWords[currentIndex];
    const card = document.getElementById('flashcard');
    card.classList.remove('flipped');

    document.getElementById('fc-uzbek').innerText = word.uzbek;
    document.getElementById('fc-uzbek-back').innerText = word.uzbek;
    document.getElementById('fc-english').innerText = word.english;
    document.getElementById('fc-type').innerText = word.type;
    document.getElementById('fc-type-back').innerText = word.type;

    const prog = ((currentIndex + 1) / currentUnitWords.length) * 100;
    document.getElementById('flashcard-progress').style.width = `${prog}%`;

    // Audio handler
    const speakBtn = document.getElementById('fc-speak');
    if (speakBtn) {
        speakBtn.onclick = (e) => {
            e.stopPropagation();
            speak(word.english);
        };
    }
}

// Event Listeners (Premium Overrides)
document.getElementById('flashcard').onclick = function (e) {
    if (!this.classList.contains('flipped')) {
        this.classList.add('flipped');
        autoNextTimer = setTimeout(() => { if (this.classList.contains('flipped')) nextCard(); }, 1500);
    } else {
        nextCard();
    }
};

document.getElementById('game-check').onclick = checkGame;
document.getElementById('game-input').onkeyup = (e) => { if (e.key === 'Enter') checkGame(); };

function checkGame() {
    const input = document.getElementById('game-input');
    const feedback = document.getElementById('game-feedback');
    const correct = currentUnitWords[currentIndex].english.toLowerCase();
    const ans = input.value.trim().toLowerCase();

    if (ans === correct) {
        score++; combo++;
        const gain = addXP(15);
        spawnXP(gain);
        feedback.innerText = "🌟 EXCELLENT!";
        feedback.style.color = "var(--success)";
        feedback.classList.remove('hidden');
        setTimeout(() => { currentIndex++; nextGameWord(); }, 800);
    } else {
        combo = 0;
        input.parentElement.classList.add('shake');
        setTimeout(() => input.parentElement.classList.remove('shake'), 400);

        feedback.innerText = `Xato! To'g'ri javob: ${correct}`;
        feedback.style.color = "var(--error)";
        feedback.classList.remove('hidden');

        // Re-queue wrong word after 5 items (or at end)
        const wrongWord = currentUnitWords[currentIndex];
        const insertIndex = Math.min(currentIndex + 6, currentUnitWords.length);
        currentUnitWords.splice(insertIndex, 0, wrongWord);

        // Auto advance after delay
        setTimeout(() => {
            currentIndex++;
            nextGameWord();
        }, 2000);
    }
}

function nextGameWord() {
    if (currentIndex >= currentUnitWords.length) return finishMode();
    const word = currentUnitWords[currentIndex];

    document.getElementById('game-uzbek').innerText = word.uzbek;
    document.getElementById('game-input').value = '';
    document.getElementById('game-input').focus();
    document.getElementById('game-correct').innerText = score;
    document.getElementById('game-remaining').innerText = currentUnitWords.length - currentIndex;
    document.getElementById('game-feedback').classList.add('hidden');

    // Auto speak option (or just bind button)
    const speakBtn = document.getElementById('game-speak');
    if (speakBtn) {
        speakBtn.onclick = () => speak(word.english);
    }
}

function finishMode() {
    const final = Math.round((score / currentUnitWords.length) * 100) || 100;

    // Save mastery if 100%
    if (final === 100 && currentUnitName) {
        stats.masteredUnits[currentUnitName] = true;
        saveStats();
    }

    document.getElementById('results-score').innerText = `${final}%`;
    if (final >= 80) confetti({ particleCount: 200, spread: 80, origin: { y: 0.6 } });
    showScreen('results');
}

const shuffle = (arr) => arr.sort(() => Math.random() - 0.5);

function renderManageList() {
    const list = document.getElementById('manage-word-list');
    if (!list) return;
    list.innerHTML = '';

    if (customUnits.length === 0) {
        list.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted); font-weight:700;">Hali hech qanday unit yaratilmadi.</div>`;
        return;
    }

    customUnits.forEach((unit, i) => {
        const item = document.createElement('div');
        item.style = "display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.05); padding:16px; border-radius:18px; margin-bottom:12px; border:1px solid var(--glass-border);";
        item.innerHTML = `
            <div>
                <b style="display:block; font-size:1.1rem;">${unit.name}</b>
                <span style="font-size:0.8rem; opacity:0.6;">${unit.words.length} ta so'z</span>
            </div>
            <button onclick="deleteCustomUnit(${i})" style="background:rgba(244,63,94,0.1); border:none; color:var(--error); padding:10px 16px; border-radius:12px; font-weight:800; cursor:pointer;">X</button>
        `;
        list.appendChild(item);
    });
}

function deleteCustomUnit(i) {
    if (confirm("Ushbu unitni o'chirmoqchimisiz?")) {
        customUnits.splice(i, 1);
        localStorage.setItem('my_custom_units', JSON.stringify(customUnits));
        renderManageList();
        parseWords();
        renderUnits();
    }
}

function bulkImport() {
    const nameText = document.getElementById('import-unit-name').value.trim();
    const text = document.getElementById('import-text').value.trim();

    if (!nameText || !text) return alert("Iltimos, unit nomi va so'zlarni kiriting!");

    const lines = text.split('\n');
    const newWords = [];

    lines.forEach(line => {
        const trimmedLine = line.trim();
        if (!trimmedLine) return;
        if (trimmedLine.includes('-') || trimmedLine.includes('–')) {
            const sep = trimmedLine.includes('–') ? '–' : '-';
            const parts = trimmedLine.split(sep);
            const en = parts[0].trim();
            const uz = parts[1].trim();
            if (en && uz) {
                newWords.push({
                    english: en.replace(/\(.*?\)/, '').trim(),
                    uzbek: uz.trim(),
                    type: 'user'
                });
            }
        }
    });

    if (newWords.length > 0) {
        customUnits.push({ name: "🌟 " + nameText, words: newWords });
        localStorage.setItem('my_custom_units', JSON.stringify(customUnits));
        alert(`${newWords.length} ta so'zli yangi unit yaratildi!`);
        document.getElementById('import-unit-name').value = '';
        document.getElementById('import-text').value = '';
        parseWords();
        renderUnits();
        renderManageList();
    } else {
        alert("Xatolik! So'zlar 'Inglizcha - Uzbekcha' formatida bo'lishi kerak.");
    }
}

// Mode Selection Initialization
document.querySelectorAll('.mode-card').forEach(card => {
    card.onclick = () => {
        const mode = card.dataset.mode;
        currentIndex = 0; score = 0; combo = 0;
        if (mode === 'flashcard') { updateFlashcard(); showScreen('flashcard'); }
        else if (mode === 'game') { currentUnitWords = shuffle([...currentUnitWords]); nextGameWord(); showScreen('game'); }
        else if (mode === 'test') startTest();
        else if (mode === 'manage') showScreen('manage');
    };
});

function startTest() {
    currentUnitWords = shuffle([...currentUnitWords]).slice(0, 15);
    nextTestQuestion();
    showScreen('test');
}

function nextTestQuestion() {
    if (currentIndex >= currentUnitWords.length) return finishMode();
    const word = currentUnitWords[currentIndex];
    document.getElementById('test-question').innerText = word.uzbek;

    let opts = shuffle([word.english, ...shuffle(units.flatMap(u => u.words).map(w => w.english)).slice(0, 3)]);
    const container = document.getElementById('test-options');
    container.innerHTML = '';

    opts.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'quiz-btn fade-up';
        // Premium Test Button Style override
        btn.style = "height:100%; min-height:100px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; font-weight:800; background:rgba(255,255,255,0.05); border:1px solid var(--glass-border); transition:0.2s;";
        btn.innerText = opt;

        btn.onclick = (e) => {
            if (opt === word.english) {
                score++; combo++;
                spawnXP(addXP(10));
                btn.style.background = "var(--success)";
                btn.style.borderColor = "var(--success)";
            } else {
                combo = 0;
                btn.style.background = "var(--error)";
                btn.style.borderColor = "var(--error)";
            }
            setTimeout(() => { currentIndex++; nextTestQuestion(); }, 600);
        };
        container.appendChild(btn);
    });
}

function showLevelUp() {
    confetti({ particleCount: 200, spread: 100 });
    const modal = document.createElement('div');
    modal.className = 'level-up-modal fade-up';
    modal.innerHTML = `
        <div class="unit-card" style="text-align:center; padding:60px 30px; display:block;">
            <div style="font-size:5rem;">⭐</div>
            <h2 style="font-size:2.5rem; font-weight:900; margin:20px 0;">LEVEL UP!</h2>
            <p style="color:var(--text-dim); margin-bottom:32px;">Siz ${stats.level}-darajaga yetdingiz!</p>
            <button class="quiz-btn" style="background:var(--accent); font-weight:900;" onclick="this.closest('.level-up-modal').remove()">BARAKALLA!</button>
        </div>
    `;
    document.body.appendChild(modal);
}

// Streak Control
function checkStreak() {
    const today = new Date().toDateString();
    if (stats.lastDate === today) return;
    if (stats.lastDate) {
        const last = new Date(stats.lastDate);
        if ((new Date() - last) / 864e5 <= 1.5) stats.streak++;
        else stats.streak = 1;
    } else stats.streak = 1;
    stats.lastDate = today;
    saveStats();
}

// Back Navs
document.getElementById('back-to-units').onclick = () => { renderUnits(); showScreen('units'); };
document.getElementById('back-from-flashcard').onclick = () => showScreen('modes');
document.getElementById('back-from-game').onclick = () => showScreen('modes');
document.getElementById('back-from-test').onclick = () => showScreen('modes');
document.getElementById('results-home').onclick = () => { renderUnits(); showScreen('units'); };

document.getElementById('fc-next').onclick = nextCard;
document.getElementById('fc-prev').onclick = () => { if (currentIndex > 0) { currentIndex--; updateFlashcard(); } };

// Custom Words (Quick Add to Default Unit)
document.getElementById('add-word-btn').onclick = () => {
    const input = document.getElementById('custom-word-input');
    if (input.value.includes('-')) {
        const [en, uz] = input.value.split('-');
        const newWord = { english: en.trim(), uzbek: uz.trim(), type: 'quick' };

        let quickUnit = customUnits.find(u => u.name === "🌟 Quick Words");
        if (!quickUnit) {
            quickUnit = { name: "🌟 Quick Words", words: [] };
            customUnits.push(quickUnit);
        }
        quickUnit.words.push(newWord);
        localStorage.setItem('my_custom_units', JSON.stringify(customUnits));
        input.value = ''; parseWords(); renderUnits();
        alert("So'z 'Quick Words' unitiga qo'shildi!");
    }
};

// Settings Logic
function openSettings() {
    document.getElementById('settings-nick').value = stats.nickname;
    showScreen('settings');
}

function saveSettingsName() {
    const nick = document.getElementById('settings-nick').value.trim();
    if (nick) {
        stats.nickname = nick;
        saveStats();
        alert("Ismingiz saqlandi!");
        showScreen('units');
    }
}

function resetAllProgress() {
    if (confirm("DIQQAT! Barcha yutuqlaringiz o'chib ketadi. Rostan ham rozimisiz?")) {
        localStorage.removeItem('me_stats');
        location.reload(); // Force reload to restart onboarding
    }
}

// Start
function init() {
    checkStreak();
    parseWords();
    renderUnits();
    updateStatsUI();

    const header = document.querySelector('header');
    const hud = document.querySelector('.user-hud');
    const nav = document.querySelector('.navbar');

    if (!stats.nickname) {
        if (header) header.classList.add('hidden');
        if (hud) hud.classList.add('hidden');
        if (nav) nav.classList.add('hidden');
        showScreen('onboarding');
    } else {
        if (header) header.classList.remove('hidden');
        if (hud) hud.classList.remove('hidden');
        if (nav) nav.classList.remove('hidden');
        showScreen('units');
    }
}

document.getElementById('onboarding-start').onclick = () => {
    const nickInput = document.getElementById('onboarding-nick');
    const nick = nickInput.value.trim();
    if (nick) {
        stats.nickname = nick;
        saveStats();

        const header = document.querySelector('header');
        const hud = document.querySelector('.user-hud');
        const nav = document.querySelector('.navbar');

        if (header) header.classList.remove('hidden');
        if (hud) hud.classList.remove('hidden');
        if (nav) nav.classList.remove('hidden');

        updateStatsUI();
        showScreen('units');
    } else {
        alert("Iltimos, ismingizni kiriting!");
    }
};

init();
