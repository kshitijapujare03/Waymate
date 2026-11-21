# WAYMATE – Personalized Travel Recommendation System

<p align="center">
  **Explore. Plan. Travel.**
  
  Your Journey, Our Recommendation.
</p>

<p align="center">
  A smart travel recommendation system designed to help users discover destinations and plan personalized trips based on their preferences.
</p>

---

## 🌍 About the Project

**WAYMATE** is a Personalized Travel Recommendation System developed to make trip planning easier, smarter, and more convenient.

The system recommends travel destinations based on user preferences such as budget, travel duration, travel type, group size, and travel companions.

It combines recommendation techniques with destination information and weather data to help users make informed travel decisions.

## 🎯 Objectives

- Provide personalized travel destination recommendations.
- Simplify the process of discovering and planning trips.
- Consider user preferences such as budget, duration, and travel type.
- Provide useful destination information and weather updates.
- Allow users to save destinations and manage their trips.

## ✨ Key Features

- **Personalized Recommendations:** Suggests destinations based on user preferences.
- **Hybrid Recommendation System:** Combines content-based, collaborative, and knowledge-based recommendation approaches.
- **Live Weather Information:** Displays current weather information for supported destinations.
- **Destination Exploration:** Browse destinations with relevant details, categories, and images.
- **User Authentication:** Register and log in to access personalized features.
- **Saved Destinations:** Save destinations for future reference.
- **Trip Management:** Organize upcoming trips and previously visited places.
- **Dynamic Packing Suggestions:** Provides packing essentials with weather-related suggestions.

## 🧠 Recommendation Approach

WAYMATE uses a hybrid recommendation approach that combines three methods:

| Technique | Purpose |
|---|---|
| Content-Based Filtering | Recommends destinations based on destination features and user preferences. |
| Collaborative Filtering | Uses available user interaction patterns to identify relevant destinations. |
| Knowledge-Based Filtering | Uses travel requirements and predefined knowledge to match suitable destinations. |

The recommendation service combines these approaches to generate personalized destination suggestions.

## 🛠️ Technology Stack

**Frontend**
- HTML5
- CSS3
- JavaScript

**Backend**
- Python
- Flask
- REST APIs

**Database**
- MySQL

**External Data Services**
- Open-Meteo API – Weather information
- Wikidata / Wikimedia – Destination information and images

**Development Tools**
- Visual Studio Code
- MySQL Workbench
- Git and GitHub

## 🏗️ System Architecture

The project follows a client-server architecture.

1. The frontend collects user preferences and displays information.
2. The Flask backend processes requests and handles application logic.
3. The recommendation service generates personalized destination suggestions.
4. The MySQL database stores destination information, user data, saved places, trips, and interactions.
5. The weather service retrieves current weather information using the Open-Meteo API.

## 🔗 Backend API Overview

| API Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Check backend status |
| `/api/register` | POST | Register a user |
| `/api/login` | POST | Authenticate a user |
| `/api/destinations` | GET | Retrieve destinations |
| `/api/destinations/popular` | GET | Retrieve popular destinations |
| `/api/destinations/<id>` | GET | Retrieve destination details |
| `/api/destinations/<id>/weather` | GET | Retrieve destination weather |
| `/api/plan-trip` | POST | Generate personalized recommendations |
| `/api/interactions` | GET | Retrieve destination interaction information |
| `/api/saved-places` | GET / POST / DELETE | Manage saved destinations |
| `/api/my-trips` | POST | Create a trip |

## 🔮 Future Enhancements

- Integration of additional travel and tourism data sources.
- Improved recommendation accuracy using more user interaction data.
- Enhanced trip planning and itinerary generation.
- Additional travel-related services and features.
- Improved user experience and interface design.

## 👩‍💻 Project Information

**Project Title:** Personalized Travel Recommendation System

**Project Name:** WAYMATE

**Project Type:** Academic / Final-Year Engineering Project

**Repository:** [WAYMATE on GitHub](https://github.com/kshitijapujare03/Waymate)

---

<p align="center">
  **WAYMATE – Explore. Plan. Travel.**
  
  Making every journey smarter and easier.
</p>
