
const destinations = [
    {
        name: "Goa",
        type: "Beach",
        description: "Famous beaches, water activities and vibrant nightlife",
        budget: 5000,
        days: 3,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Jaipur",
        type: "Historical & Cultural",
        description: "Forts, palaces, markets and rich Rajasthani culture",
        budget: 4500,
        days: 3,
        rating: 4.4,
        image: "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Kerala Backwaters",
        type: "Nature",
        description: "Peaceful backwaters, houseboats and beautiful natural scenery",
        budget: 6000,
        days: 3,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Manali",
        type: "Hill Station",
        description: "Mountains, valleys, scenic views and adventure activities",
        budget: 6000,
        days: 4,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Agra",
        type: "Historical",
        description: "Famous for the Taj Mahal and Mughal architecture",
        budget: 3500,
        days: 2,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Hampi",
        type: "Historical",
        description: "Ancient ruins, temples and unique landscapes",
        budget: 4000,
        days: 2,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1600100397608-f0102f7a6f9d?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Amritsar",
        type: "Religious & Historical",
        description: "Golden Temple, Jallianwala Bagh and Punjabi culture",
        budget: 4000,
        days: 2,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1609947017136-9daf32a5eb16?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Rishikesh",
        type: "Adventure & Spiritual",
        description: "River rafting, yoga, temples and mountain views",
        budget: 4500,
        days: 3,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1597074866923-dc0589150358?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Ladakh",
        type: "Adventure & Nature",
        description: "High-altitude landscapes, monasteries and mountain passes",
        budget: 10000,
        days: 5,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1518002054494-3a6f94352e9d?auto=format&fit=crop&w=800&q=80"
    },
    {
        name: "Meghalaya",
        type: "Nature",
        description: "Waterfalls, caves, forests and living root bridges",
        budget: 7000,
        days: 4,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1622308644420-b20142dc993c?auto=format&fit=crop&w=800&q=80"
    }
];

let currentPage = 1;
const cardsPerPage = 6;
let filteredDestinations = [...destinations];


// OPEN DESTINATION FROM EXPLORE
function openDestination(destination) {

    // Mark that the destination was opened from Explore
    localStorage.setItem("destinationSource", "explore");

    // Save selected destination details
    localStorage.setItem(
        "selectedDestination",
        JSON.stringify(destination)
    );

    // Open destination page with Explore source
    window.location.href = "destination.html?source=explore";
}


// DISPLAY DESTINATIONS
function displayDestinations() {

    const grid = document.getElementById("destinationGrid");
    const noResults = document.getElementById("noResults");

    grid.innerHTML = "";

    const start = (currentPage - 1) * cardsPerPage;
    const end = start + cardsPerPage;

    const currentDestinations =
        filteredDestinations.slice(start, end);

    if (currentDestinations.length === 0) {
        noResults.style.display = "block";
        document.getElementById("pagination").innerHTML = "";
        return;
    }

    noResults.style.display = "none";

    currentDestinations.forEach(destination => {

        const card = document.createElement("div");

        card.className = "explore-destination-card";

        card.innerHTML = `
            <img src="${destination.image}" alt="${destination.name}">

            <div class="destination-card-content">

                <h3>${destination.name}</h3>

                <p class="destination-type">
                    ${destination.type}
                </p>

                <p class="destination-description">
                    ${destination.description}
                </p>

                <div class="destination-info-row">

                    <span>
                        ₹${destination.budget.toLocaleString("en-IN")}
                    </span>

                    <span>
                        ⭐ ${destination.rating}
                    </span>

                </div>

                <p class="destination-days">
                    ${destination.days} days recommended
                </p>

            </div>
        `;

        card.addEventListener("click", function() {
            openDestination(destination);
        });

        grid.appendChild(card);
    });

    displayPagination();
}


// DISPLAY PAGINATION
function displayPagination() {

    const pagination =
        document.getElementById("pagination");

    pagination.innerHTML = "";

    const totalPages =
        Math.ceil(filteredDestinations.length / cardsPerPage);

    if (totalPages <= 1) {
        return;
    }

    for (let i = 1; i <= totalPages; i++) {

        const button = document.createElement("button");

        button.textContent = i;

        if (i === currentPage) {
            button.classList.add("active-page");
        }

        button.onclick = function() {
            currentPage = i;
            displayDestinations();
        };

        pagination.appendChild(button);
    }
}


// APPLY FILTERS AND SORTING
function applyFilters() {

    const searchValue =
        document.getElementById("searchInput")
        .value
        .toLowerCase()
        .trim();

    const selectedType =
        document.getElementById("typeFilter").value;

    const selectedBudget =
        document.getElementById("budgetFilter").value;

    const selectedDuration =
        document.getElementById("durationFilter").value;

    const selectedSort =
        document.getElementById("sortFilter").value;

    filteredDestinations = destinations.filter(destination => {

        const matchesSearch =
            destination.name
            .toLowerCase()
            .includes(searchValue);

        const matchesType =
            selectedType === "all" ||
            destination.type === selectedType;

        const matchesBudget =
            selectedBudget === "all" ||
            destination.budget <= Number(selectedBudget);

        const matchesDuration =
            selectedDuration === "all" ||
            destination.days === Number(selectedDuration);

        return (
            matchesSearch &&
            matchesType &&
            matchesBudget &&
            matchesDuration
        );
    });

    if (selectedSort === "priceLow") {
        filteredDestinations.sort(
            (a, b) => a.budget - b.budget
        );
    }

    if (selectedSort === "priceHigh") {
        filteredDestinations.sort(
            (a, b) => b.budget - a.budget
        );
    }

    if (selectedSort === "ratingHigh") {
        filteredDestinations.sort(
            (a, b) => b.rating - a.rating
        );
    }

    currentPage = 1;

    displayDestinations();
}


// SEARCH DESTINATIONS
function searchDestinations() {
    applyFilters();
}


// SEARCH WHEN ENTER IS PRESSED
document
    .getElementById("searchInput")
    .addEventListener("keydown", function(event) {

        if (event.key === "Enter") {
            searchDestinations();
        }

    });


// INITIAL DISPLAY
displayDestinations();
