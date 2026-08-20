console.log("login.js chargé");
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("loginForm");

  if (!form) {
    console.error("Formulaire login introuvable");
    return;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault(); // ⛔ empêche le refresh

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email: email,
        password: password
      })
    })
      .then(response => response.json())
      .then(data => {
        if (data.user_id) {
          // ✅ Login réussi
          localStorage.setItem("user_id", data.user_id);
          alert("Login réussi ✅");

          // 🔁 redirection
          window.location.href = "dashboard.html";
        } else {
          alert(data.error || "Login échoué ❌");
        }
      })
      .catch(error => {
        console.error(error);
        alert("Erreur serveur");
      });
  });
});

