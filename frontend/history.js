const user_id = localStorage.getItem("user_id");

if (!user_id) {
    alert("Utilisateur non connecté");
    window.location.href = "login.html";
}

/* ======================
   HISTORIQUE MÉTRIQUES
====================== */
fetch(`http://127.0.0.1:5000/metrics/history/${user_id}`)
    .then(res => res.json())
    .then(data => {
        const table = document.getElementById("metricsTable");

        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${new Date(row.created_at).toLocaleString()}</td>
                <td>${row.cpu}</td>
                <td>${row.ram}</td>
                <td>${row.disk}</td>
            `;
            table.appendChild(tr);
        });
    })
    .catch(err => {
        console.error("Erreur métriques :", err);
    });

/* ======================
   HISTORIQUE ALERTES
====================== */
fetch(`http://127.0.0.1:5000/alerts/history/${user_id}`)
    .then(res => res.json())
    .then(data => {
        const table = document.getElementById("alertsTable");

        data.forEach(row => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${new Date(row.created_at).toLocaleString()}</td>
                <td>${row.type}</td>
                <td>
                    <span class="badge ${
                        row.level === "critical" ? "bg-danger" : "bg-warning text-dark"
                    }">
                        ${row.level}
                    </span>
                </td>
                <td>${row.message}</td>
            `;

            table.appendChild(tr);
        });
    })
    .catch(err => {
        console.error("Erreur alertes :", err);
    });
