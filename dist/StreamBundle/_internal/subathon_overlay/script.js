document.addEventListener('DOMContentLoaded', async () => {
    // Lade zuerst die Einstellungen
    const settings = await getSettings();

    // Filtere die Regeln basierend auf den Einstellungen
    const ruleElements = Array.from(document.querySelectorAll('.rule-item'));
    const activeRules = [];

    if (settings.show_subs) {
        const rule = ruleElements.find(el => el.dataset.rule === 'subs');
        if (rule) {
            rule.textContent = settings.text_subs;
            activeRules.push(rule);
        }
    }
    if (settings.show_followers) {
        const rule = ruleElements.find(el => el.dataset.rule === 'followers');
        if (rule) {
            rule.textContent = settings.text_followers;
            activeRules.push(rule);
        }
    }
    if (settings.show_coins) {
        const rule = ruleElements.find(el => el.dataset.rule === 'coins');
        if (rule) {
            rule.textContent = settings.text_coins;
            activeRules.push(rule);
        }
    }

    // Entferne ungenutzte Regel-Elemente aus dem DOM
    ruleElements.forEach(el => {
        if (!activeRules.includes(el)) {
            el.remove();
        }
    });

    // Starte die Animation nur, wenn es aktive Regeln gibt
    if (activeRules.length > 0) {
        animateRules(activeRules);
    }
});

async function getSettings() {
    try {
        const response = await fetch('/subathon_overlay/settings.json');
        if (!response.ok) {
            // Wenn die Datei nicht gefunden wird, gib Standardwerte zurück
            return getDefaultSettings();
        }
        return await response.json();
    } catch (error) {
        console.error("Fehler beim Laden der Einstellungen, verwende Standardwerte.", error);
        return getDefaultSettings();
    }
}

function getDefaultSettings() {
    return {
        show_subs: true,
        text_subs: "+10 Min pro Sub",
        show_followers: true,
        text_followers: "+10 Sek pro Follower",
        show_coins: true,
        text_coins: "+0.7 Sek pro Münze"
    };
}

function animateRules(rules) {
    let currentIndex = 0;
    const displayDuration = 5000; // 5 Sekunden

    function cycle() {
        if (rules.length === 0) return;

        // Verstecke alle Regeln
        rules.forEach(rule => {
            rule.classList.remove('show');
            rule.classList.add('hide');
        });

        // Zeige die aktuelle Regel
        const currentRule = rules[currentIndex];
        currentRule.classList.remove('hide');
        currentRule.classList.add('show');

        // Gehe zur nächsten Regel
        currentIndex = (currentIndex + 1) % rules.length;

        // Wiederhole den Zyklus
        setTimeout(cycle, displayDuration);
    }

    cycle(); // Starte den Animationszyklus
}