require("dotenv").config();
const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
res.send("WayMate Backend is Running!");
});

// Destination Database
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
// Weather API Function
async function getWeather(city) {
    const apiKey = process.env.OPENWEATHER_API_KEY;

    const url = `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`;

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
app.post("/recommend", async (req, res) => {

const { people, budget, days, destination, weather,location } = req.body;
let weatherData = null;

if (location) {
    try {
        weatherData = await getWeather(location);
    } catch (error) {
        console.log("Weather API Error:", error.message);
    }
}
// Convert input values into numbers
const userBudget = Number(budget);
const userDays = Number(days);

// Find destinations that fit the user's budget and days
let suitableDestinations = destinations.filter(place =>
    userBudget >= place.minBudget &&
    userDays >= place.recommendDays
);

// If user has selected a destination
if (destination && destination !== "not decided") {
    suitableDestinations = suitableDestinations.filter(place =>
        place.name.toLowerCase() === destination.toLowerCase()
    );
}

// If no exact match is found
if (suitableDestinations.length === 0) {
    return res.json({
        success: false,
        message: "No suitable destination found for your budget and number of days."
    });
}

// Select highest-rated suitable destination
suitableDestinations.sort((a, b) => b.rating - a.rating);

const bestDestination = suitableDestinations[0];

res.json({
    success: true,
    recommendation: bestDestination.name,
    details: bestDestination,
    weather: weatherData
});


});

const PORT = 5000;

app.listen(PORT, () => {
console.log(`Server running on http://localhost:${PORT}`);
});
