document.addEventListener('DOMContentLoaded', () => {
    const rules = document.querySelectorAll('.rule-item');
    let currentIndex = 0;

    const displayDuration = 5000; // Dauer, die jede Regel angezeigt wird (8 Sekunden)

    function showRule(element) {
        element.classList.remove('hide');
        element.classList.add('show');
    }

    function hideRule(element) {
        element.classList.remove('show');
        element.classList.add('hide');
    }

    function animateRules() {
        rules.forEach(hideRule);
        showRule(rules[currentIndex]);

        setTimeout(() => {
            currentIndex = (currentIndex + 1) % rules.length;
            animateRules();
        }, displayDuration);
    }

    animateRules();
});