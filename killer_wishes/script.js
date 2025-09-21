const api_url = 'http://127.0.0.1:5000/killer_wishes/data';
const wishTextElements = document.querySelectorAll('.wish-text');
const wishUserElements = document.querySelectorAll('.wish-user');

async function getWishes() {
    const response = await fetch(api_url);
    const data = await response.json();

    if (data.length > 0) {
        // Zeige die Wünsche an
        for (let i = 0; i < 2; i++) {
            if (data[i]) {
                wishTextElements[i].textContent = data[i].wunsch;
                wishUserElements[i].textContent = `~ ${data[i].user_name}`;
            } else {
                wishTextElements[i].textContent = '';
                wishUserElements[i].textContent = '';
            }
        }
    } else {
        // Zeige die Leermeldung an
        wishTextElements[0].textContent = "gib !wish <Killer> ein";
        wishUserElements[0].textContent = "um deinen Killer zu sehen";
        if (wishTextElements[1]) {
            wishTextElements[1].textContent = '';
            wishUserElements[1].textContent = '';
        }
    }
}

getWishes();
setInterval(getWishes, 1000); // Häufiger aktualisieren, um auf Hotkey-Änderungen zu reagieren