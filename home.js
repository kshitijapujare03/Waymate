async function loadPopularDestinations() {

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/api/destinations/popular"
        );

        const data = await response.json();

        if (!response.ok) {
            console.error("API Error:", data);
            return;
        }

        console.log("Popular destinations:", data);

    } catch (error) {

        console.error("Backend connection failed:", error);

    }
}

loadPopularDestinations();