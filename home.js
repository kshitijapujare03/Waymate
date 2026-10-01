const API_URL = "http://127.0.0.1:5000";


async function loadPopularDestinations() {

    try {

        const response = await fetch(
            `${API_URL}/api/destinations/popular`
        );

        const data = await response.json();

        if (!response.ok) {

            console.error(
                "Failed to load popular destinations:",
                data
            );

            return;
        }


        const destinations =
            data.destinations || [];


        console.log(
            "Popular destinations from backend:",
            destinations
        );


        const cards =
            document.querySelectorAll(
                ".destination-card"
            );


        destinations
            .slice(0, 4)
            .forEach(function(destination, index) {

                const card = cards[index];

                if (!card) {
                    return;
                }


                const image =
                    card.querySelector("img");

                const title =
                    card.querySelector("h3");

                const description =
                    card.querySelector("p");

                const button =
                    card.querySelector(".explore-btn");


                // -----------------------------
                // IMAGE
                // -----------------------------

                image.src =
                    destination.image_url || "";

                image.alt =
                    destination.name;


                // -----------------------------
                // NAME
                // -----------------------------

                title.textContent =
                    destination.name;


                // -----------------------------
                // DESCRIPTION
                // -----------------------------

                description.textContent =
                    destination.description || "";


                // -----------------------------
                // BUTTON
                // -----------------------------

                button.textContent =
                    `Explore ${destination.name} →`;


                // -----------------------------
                // CLICK
                // -----------------------------

                button.onclick =
                    async function(event) {

                        event.preventDefault();


                        // Save selected destination
                        const selectedDestination = {

                            id:
                                destination.id,

                            name:
                                destination.name,

                            type:
                                destination.destination_type,

                            description:
                                destination.description,

                            budget:
                                destination.budget_min,

                            budget_min:
                                destination.budget_min,

                            budget_max:
                                destination.budget_max,

                            rating:
                                destination.rating,

                            image:
                                destination.image_url,

                            location:
                                destination.location,

                            weather:
                                destination.weather,

                            packing_essentials:
                                destination.packing_essentials

                        };


                        localStorage.setItem(
                            "selectedDestination",
                            JSON.stringify(
                                selectedDestination
                            )
                        );
                        localStorage.setItem(
    "destinationSource",
    "home"
);

                        // -----------------------------
                        // RECORD INTERACTION
                        // -----------------------------

                        try {

                            await fetch(
                                `${API_URL}/api/destinations/${destination.id}/interaction`,
                                {
                                    method: "POST",

                                    headers: {
                                        "Content-Type":
                                            "application/json"
                                    },

                                    body: JSON.stringify({
                                        interaction_type:
                                            "click"
                                    })
                                }
                            );

                        }

                        catch (error) {

                            console.error(
                                "Interaction error:",
                                error
                            );

                        }


                        // -----------------------------
                        // OPEN DESTINATION PAGE
                        // -----------------------------

                        window.location.href =
                            "destination.html";

                    };

            });

    }

    catch (error) {

        console.error(
            "Error connecting to backend:",
            error
        );

    }

}


// Load when Home opens

document.addEventListener(
    "DOMContentLoaded",
    loadPopularDestinations
);