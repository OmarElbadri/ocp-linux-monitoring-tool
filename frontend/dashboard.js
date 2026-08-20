const user_id = localStorage.getItem("user_id");
if (!user_id) {
    alert("Utilisateur non connecté");
    window.location.href = "login.html";
}


let labels = [];
let cpuData = [];
let ramData = [];
let diskData = [];

const cpuChart = new Chart(document.getElementById("cpuChart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "CPU (%)",
            data: cpuData,
            borderColor: "red",
            fill: false
        }]
    }
});

const ramChart = new Chart(document.getElementById("ramChart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "RAM (%)",
            data: ramData,
            borderColor: "blue",
            fill: false
        }]
    }
});

const diskChart = new Chart(document.getElementById("diskChart"), {
    type: "line",
    data: {
        labels: labels,
        datasets: [{
            label: "DISK (%)",
            data: diskData,
            borderColor: "green",
            fill: false
        }]
    }
});

function loadMetrics() {
    fetch(`http://127.0.0.1:5000/metrics/history/${user_id}`)
        .then(res => res.json())
        .then(data => {
            labels.length = 0;
            cpuData.length = 0;
            ramData.length = 0;
            diskData.length = 0;

            data.reverse().forEach(row => {
                labels.push(new Date(row.created_at).toLocaleTimeString());
                cpuData.push(row.cpu);
                ramData.push(row.ram);
                diskData.push(row.disk);
            });

            cpuChart.update();
            ramChart.update();
            diskChart.update();
        })
        .catch(err => {
            console.error("Erreur chargement metrics :", err);
        });
}


// Charger au démarrage
loadMetrics();

// Rafraîchissement automatique toutes les 5 secondes
setInterval(loadMetrics, 3000);

function logout() {
    localStorage.removeItem("user_id");
    window.location.href = "login.html";
}

document.getElementById("historyBtn").addEventListener("click", () => {
    window.location.href = "history.html";
});

// ── Génération du token d'installation ────────────────────────────────────────
document.getElementById("tokenBtn").addEventListener("click", () => {
    const btn = document.getElementById("tokenBtn");

    // Récupérer user_id au moment du clic (pas au chargement)
    const uid = localStorage.getItem("user_id");
    console.log("user_id au clic :", uid);

    if (!uid) {
        alert("❌ Impossible de récupérer l'identifiant utilisateur.\n\nCause probable : le navigateur bloque localStorage (mode privé ou Edge Tracking Prevention).\n\nSolution : désactivez la protection contre le suivi dans Edge, ou utilisez Chrome/Firefox.");
        return;
    }

    btn.disabled = true;
    btn.textContent = "⏳ Génération en cours...";

    fetch("http://127.0.0.1:5000/agents/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: uid })
    })
    .then(res => {
        if (!res.ok) throw new Error("Réponse serveur : " + res.status);
        return res.json();
    })
    .then(data => {
        const token = data.token;
        console.log("TOKEN =", token);

        document.getElementById("tokenValue").textContent = token;
        document.getElementById("tokenBox").classList.remove("d-none");

        btn.disabled = false;
        btn.textContent = "🔑 Générer le token d'installation";
    })
    .catch(err => {
        console.error("Erreur génération token :", err);
        alert("❌ Erreur lors de la génération du token. Vérifiez que le backend est lancé.");
        btn.disabled = false;
        btn.textContent = "🔑 Générer le token d'installation";
    });
});

// Bouton copier le token
document.getElementById("copyBtn").addEventListener("click", () => {
    const token = document.getElementById("tokenValue").textContent;
    navigator.clipboard.writeText(token).then(() => {
        const copyBtn = document.getElementById("copyBtn");
        copyBtn.textContent = "✅ Copié !";
        setTimeout(() => { copyBtn.textContent = "📋 Copier le token"; }, 2000);
    });
});
