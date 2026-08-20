function register() {
    const data = {
        username: document.getElementById("username").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
        whatsapp: document.getElementById("whatsapp").value
    };

    fetch("http://localhost:5000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(res => {
        const msg = document.getElementById("msg");
        if (res.status) {
            msg.innerHTML = "Inscription réussie. <a href='login.html'>Se connecter</a>";
            msg.className = "text-success text-center";
        } else {
            msg.innerText = res.error;
            msg.className = "text-danger text-center";
        }
    });
}
