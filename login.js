document.querySelector("#loginForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const email = document.querySelector("#email").value.trim();
    const password = document.querySelector("#password").value;

    try {
        const response = await fetch("http://127.0.0.1:5000/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Login successful!");

            localStorage.setItem("user_id", data.user.id);
            localStorage.setItem("user_name", data.user.full_name);

            window.location.href = "home.html";
        } else {
            alert(data.message || "Login failed.");
        }

    } catch (error) {
        console.error("Login error:", error);
        alert("Cannot connect to the backend.");
    }
});