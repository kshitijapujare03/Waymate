
const form = document.getElementById("travelForm");
const result = document.getElementById("result");

// Safely display dynamic text
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function (char) {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };
        return entities[char];
    });
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // 1. GET USER INPUT
    const people = Number(document.getElementById("people").value);
    const budget = Number(document.getElementById("budget").value);
    const days = Number(document.getElementById("days").value);

    const destination = document.getElementById("destination").value;
    const weatherPreference = document.getElementById("weather").value;
    const startingCity = document.getElementById("location").value.trim();

    result.innerHTML = "<p>Finding the best destinations for you...</p>";

    try {
        // 2. SEND DATA TO FLASK BACKEND
        const response = await fetch(
            "http://localhost:5001/api/plan-trip",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    startingCity: startingCity,
                    travelDays: days,
                    budget: budget,
                    travelType: "Any",
                    travellers: people,
                    travelCompany: "Not specified",
                    preferredDestination: destination,
                    weatherPreference: weatherPreference
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to generate recommendations"
            );
        }

        const recommendations = data.recommendations || [];

        if (recommendations.length === 0) {
            result.innerHTML = "<h3>No suitable destinations found.</h3>";
            return;
        }

        // 3. DISPLAY RECOMMENDATIONS
        let recommendationHTML = `
            <h2>Recommended Destinations</h2>
            <p>${escapeHTML(
                data.message || "Recommendations generated successfully."
            )}</p>
        `;

        recommendations.forEach((place, index) => {
            const name = escapeHTML(
                place.name || place.destination_name || "Destination"
            );

            const type = escapeHTML(
                place.destination_type || place.type || "Not available"
            );

            const description = escapeHTML(
                place.description || "No description available"
            );

            const minBudget = Number(
                place.budget_min ?? place.budget ?? 0
            );

            const maxBudget = Number(place.budget_max ?? 0);

            const recommendedDays =
                place.recommended_days || place.days || "Not available";

            // Show actual rating only when a positive rating exists
            const ratingValue = Number(place.rating);

            const ratingDisplay =
                Number.isFinite(ratingValue) && ratingValue > 0
                    ? `⭐ ${ratingValue.toFixed(1)} / 5`
                    : "Not Rated Yet";

            // Read actual hybrid match percentage from backend
            const matchValue = Number(
                place.match_percentage ?? place.matchPercentage ?? 0
            );

            const matchDisplay = Number.isFinite(matchValue)
                ? `${matchValue.toFixed(1)}%`
                : "Not available";

            const image = place.image_url || place.image || "";

            const explanation = escapeHTML(
                place.match_explanation ||
                "Recommended based on overall destination suitability."
            );

            const imageHTML = image
                ? `
                    <img
                        src="${escapeHTML(image)}"
                        alt="${name}"
                        style="max-width:250px; width:100%; border-radius:10px;"
                        onerror="this.style.display='none'"
                    >
                `
                : "";

            recommendationHTML += `
                <div class="recommendation-card">

                    <h3>${index + 1}. ${name}</h3>

                    ${imageHTML}

                    <p>
                        <strong>Type:</strong>
                        ${type}
                    </p>

                    <p>
                        <strong>Description:</strong>
                        ${description}
                    </p>

                    <p>
                        <strong>Budget:</strong>
                        ₹${minBudget.toLocaleString("en-IN")}
                        ${maxBudget > 0
                            ? " - ₹" + maxBudget.toLocaleString("en-IN")
                            : ""}
                    </p>

                    <p>
                        <strong>Recommended Days:</strong>
                        ${escapeHTML(recommendedDays)}
                    </p>

                    <p>
                        <strong>Rating:</strong>
                        ${ratingDisplay}
                    </p>

                    <p>
                        <strong>Match:</strong>
                        ${matchDisplay}
                    </p>

                    <p>
                        <strong>Why recommended:</strong>
                        ${explanation}
                    </p>

                </div>

                <hr>
            `;
        });

        result.innerHTML = recommendationHTML;

        // 4. FETCH CURRENT WEATHER OF STARTING CITY
        if (startingCity) {
            try {
                const weatherResponse = await fetch(
                    `http://localhost:5001/api/weather?city=${encodeURIComponent(startingCity)}`
                );

                const weatherData = await weatherResponse.json();

                if (!weatherResponse.ok) {
                    throw new Error(
                        weatherData.error || "Weather unavailable"
                    );
                }

                result.innerHTML += `
                    <div class="weather-card">

                        <h2>
                            Current Weather in
                            ${escapeHTML(weatherData.city || startingCity)}
                        </h2>

                        <p>
                            <strong>Temperature:</strong>
                            ${escapeHTML(weatherData.temperature)} °C
                        </p>

                        <p>
                            <strong>Weather:</strong>
                            ${escapeHTML(weatherData.description)}
                        </p>

                        <p>
                            <strong>Humidity:</strong>
                            ${escapeHTML(weatherData.humidity)}%
                        </p>

                        <p>
                            <strong>Your Weather Preference:</strong>
                            ${escapeHTML(weatherPreference)}
                        </p>

                    </div>
                `;

            } catch (weatherError) {
                result.innerHTML += `
                    <p>Current weather information is unavailable.</p>
                `;

                console.error("Weather Error:", weatherError);
            }
        }

    } catch (error) {
        result.innerHTML = `
            <h3>Something went wrong!</h3>
            <p>${escapeHTML(error.message)}</p>
            <p>Please check whether the backend server is running on port 5001.</p>
        `;

        console.error("Backend Error:", error);
    }
});
