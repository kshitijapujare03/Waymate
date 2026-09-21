const form = document.getElementById("travelForm");
const result = document.getElementById("result");

form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const people = document.getElementById("people").value;
    const budget = document.getElementById("budget").value;
    const days = document.getElementById("days").value;
    const destination = document.getElementById("destination").value;
    const weather = document.getElementById("weather").value;
    const location = document.getElementById("location").value;

    try {
        const response = await fetch("http://localhost:5000/recommend", {
            method: "POST",  
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                people: people,
                budget: budget,
                days: days,
                destination: destination,
                weather: weather,
                location: location
            })
        });

        const data = await response.json();

        if (data.success) {
            result.innerHTML = `
                <h2>Recommended Destination</h2>
                <h3>${data.details.name}</h3>
                <p><strong>Type:</strong> ${data.details.type}</p>
                <p><strong>Description:</strong> ${data.details.description}</p>
                <p><strong>Minimum Budget:</strong> ₹${data.details.minBudget}</p>
                <p><strong>Recommended Days:</strong> ${data.details.recommendDays}</p>
                <p><strong>Rating:</strong> ⭐ ${data.details.rating}/5</p>
                <p><strong>Weather:</strong> ${data.weather?.weather || "Not available"}</p>
<p><strong>Temperature:</strong> ${data.weather?.temperature || "Not available"} °C</p>
<p><strong>Weather Description:</strong> ${data.weather?.description || "Not available"}</p>
            `;
        } else {
            result.innerHTML = `
                <h3>No suitable destination found</h3>
                <p>${data.message}</p>
            `;
        }

    } catch (error) {
        result.innerHTML = `
            <p>Backend connection error. Please make sure the server is running.</p>
        `;

        console.error(error);
    }
});
