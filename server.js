require("dotenv").config();

const express = require("express");
const cors = require("cors");
const ratings = require("./ratings");

const app = express();

app.use(cors());
app.use(express.json());


// ==========================================
// HOME / TEST ROUTE
// ==========================================

app.get("/", (req, res) => {
    res.send("WayMate Backend is Running!");
});


// ==========================================
// DESTINATION DATA
// ==========================================

const destinations = [
    {
        name: "Goa",
        type: "Beach",
        description: "Famous beaches, water activities and vibrant nightlife",
        minBudget: 5000,
        recommendDays: 3,
        rating: 4.5
    },

    {
        name: "Jaipur",
        type: "Historical & Cultural",
        description: "Forts, palaces, markets and rich Rajasthani culture",
        minBudget: 4500,
        recommendDays: 3,
        rating: 4.4
    },

    {
        name: "Kerala Backwaters",
        type: "Nature",
        description: "Peaceful backwaters, houseboats and beautiful natural scenery",
        minBudget: 6000,
        recommendDays: 3,
        rating: 4.6
    },

    {
        name: "Manali",
        type: "Hill Station",
        description: "Mountains, valleys, scenic views and adventure activities",
        minBudget: 6000,
        recommendDays: 4,
        rating: 4.5
    },

    {
        name: "Agra",
        type: "Historical",
        description: "Famous for the Taj Mahal and Mughal architecture",
        minBudget: 3500,
        recommendDays: 2,
        rating: 4.5
    },

    {
        name: "Hampi",
        type: "Historical",
        description: "Ancient ruins, temples and unique landscapes",
        minBudget: 4000,
        recommendDays: 2,
        rating: 4.6
    },

    {
        name: "Amritsar",
        type: "Religious & Historical",
        description: "Golden Temple, Jallianwala Bagh and Punjabi culture",
        minBudget: 4000,
        recommendDays: 2,
        rating: 4.7
    },

    {
        name: "Rishikesh",
        type: "Adventure & Spiritual",
        description: "River rafting, yoga, temples and mountain views",
        minBudget: 4500,
        recommendDays: 3,
        rating: 4.5
    },

    {
        name: "Ladakh",
        type: "Adventure & Nature",
        description: "High-altitude landscapes, monasteries and mountain passes",
        minBudget: 10000,
        recommendDays: 5,
        rating: 4.7
    },

    {
        name: "Meghalaya",
        type: "Nature",
        description: "Waterfalls, caves, forests and living root bridges",
        minBudget: 7000,
        recommendDays: 4,
        rating: 4.6
    }
];


// ==========================================
// WEATHER API FUNCTION
// ==========================================

async function getWeather(city) {

    const apiKey = process.env.OPENWEATHER_API_KEY;

    const url =
        `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`;

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error("Weather data not found");
    }

    const data = await response.json();

    return {
        city: data.name,
        temperature: data.main.temp,
        weather: data.weather[0].main,
        description: data.weather[0].description
    };
}


// ==========================================
// CONTENT-BASED FILTERING
// ==========================================

function calculateContentScore(
    place,
    userBudget,
    userDays,
    userDestination
) {

    let budgetScore = 0;
    let daysScore = 0;
    let destinationScore = 0;


    // --------------------------------------
    // BUDGET SCORE
    // --------------------------------------

    if (userBudget >= place.minBudget) {

        const budgetDifference =
            userBudget - place.minBudget;

        if (budgetDifference <= 2000) {

            budgetScore = 1;

        } else if (budgetDifference <= 5000) {

            budgetScore = 0.8;

        } else {

            budgetScore = 0.6;
        }
    }


    // --------------------------------------
    // DAYS SCORE
    // --------------------------------------

    if (userDays >= place.recommendDays) {

        const extraDays =
            userDays - place.recommendDays;

        if (extraDays === 0) {

            daysScore = 1;

        } else if (extraDays <= 2) {

            daysScore = 0.8;

        } else {

            daysScore = 0.6;
        }
    }


    // --------------------------------------
    // DESTINATION PREFERENCE
    // --------------------------------------

    if (
        !userDestination ||
        userDestination.toLowerCase() === "not decided"
    ) {

        destinationScore = 0.5;

    } else if (
        place.name.toLowerCase() ===
        userDestination.toLowerCase()
    ) {

        destinationScore = 1;

    } else {

        destinationScore = 0;
    }


    // --------------------------------------
    // CONTENT SCORE
    // --------------------------------------

    const contentScore =
        (budgetScore * 0.4) +
        (daysScore * 0.3) +
        (destinationScore * 0.3);


    return Number(contentScore.toFixed(2));
}


// ==========================================
// COLLABORATIVE / RATING SCORE
// ==========================================

function calculateCollaborativeScore(destinationName) {

    const destinationRatings =
        ratings.filter(
            item =>
                item.destination.toLowerCase() ===
                destinationName.toLowerCase()
        );


    // No rating data
    if (destinationRatings.length === 0) {

        return 0;
    }


    // Calculate total ratings

    const totalRating =
        destinationRatings.reduce(
            (sum, item) => sum + item.rating,
            0
        );


    // Calculate average rating

    const averageRating =
        totalRating / destinationRatings.length;


    // Convert 1-5 rating into 0-1 score

    const collaborativeScore =
        averageRating / 5;


    return Number(
        collaborativeScore.toFixed(2)
    );
}


// ==========================================
// RECOMMENDATION API
// ==========================================

app.post("/recommend", async (req, res) => {

    try {

        const {
            people,
            budget,
            days,
            destination,
            weather,
            location
        } = req.body;


        // ----------------------------------
        // Convert input values
        // ----------------------------------

        const userBudget = Number(budget);
        const userDays = Number(days);
        const userPeople = Number(people);


        // ----------------------------------
        // Weather Data
        // ----------------------------------

        let weatherData = null;


        if (location) {

            try {

                weatherData =
                    await getWeather(location);

            } catch (error) {

                console.log(
                    "Weather API Error:",
                    error.message
                );

            }
        }


        // ----------------------------------
        // FILTER BY BUDGET AND DAYS
        // ----------------------------------

        let suitableDestinations =
            destinations.filter(place =>
                userBudget >= place.minBudget &&
                userDays >= place.recommendDays
            );


        // ----------------------------------
        // DESTINATION PREFERENCE
        // ----------------------------------

        if (
            destination &&
            destination.toLowerCase() !== "not decided"
        ) {

            const selectedDestination =
                suitableDestinations.filter(
                    place =>
                        place.name.toLowerCase() ===
                        destination.toLowerCase()
                );


            if (selectedDestination.length > 0) {

                suitableDestinations =
                    selectedDestination;
            }
        }


        // ----------------------------------
        // CHECK IF DESTINATION EXISTS
        // ----------------------------------

        if (suitableDestinations.length === 0) {

            return res.json({

                success: false,

                message:
                    "No suitable destination found for your budget and number of days."

            });
        }


        // ----------------------------------
        // CALCULATE CONTENT + COLLABORATIVE
        // ----------------------------------

        suitableDestinations =
            suitableDestinations.map(place => {


                const contentScore =
                    calculateContentScore(
                        place,
                        userBudget,
                        userDays,
                        destination
                    );


                const collaborativeScore =
                    calculateCollaborativeScore(
                        place.name
                    );


                // ----------------------------------
                // HYBRID SCORE
                // ----------------------------------

                const hybridScore =
                    (contentScore * 0.6) +
                    (collaborativeScore * 0.4);


                return {

                    ...place,

                    contentScore:
                        Number(contentScore.toFixed(2)),

                    collaborativeScore:
                        Number(collaborativeScore.toFixed(2)),

                    hybridScore:
                        Number(hybridScore.toFixed(2))
                };

            });


        // ----------------------------------
        // SORT BY HYBRID SCORE
        // ----------------------------------

        suitableDestinations.sort(
            (a, b) =>
                b.hybridScore -
                a.hybridScore
        );


        // ----------------------------------
        // BEST DESTINATION
        // ----------------------------------

        const bestDestination =
            suitableDestinations[0];


        // ----------------------------------
        // FINAL RESPONSE
        // ----------------------------------

        res.json({

            success: true,

            recommendation:
                bestDestination.name,

            details:
                bestDestination,

            contentScore:
                bestDestination.contentScore,

            collaborativeScore:
                bestDestination.collaborativeScore,

            hybridScore:
                bestDestination.hybridScore,

            weather:
                weatherData
        });


    } catch (error) {

        console.error(
            "Recommendation Error:",
            error
        );


        res.status(500).json({

            success: false,

            message:
                "Something went wrong on the server."

        });

    }

});


// ==========================================
// START SERVER
// ==========================================

const PORT = 5000;

app.listen(PORT, () => {

    console.log(
        `Server running on http://localhost:${PORT}`
    );

});

