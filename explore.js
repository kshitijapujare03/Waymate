const API_URL = "http://127.0.0.1:5000";

let destinations = [];

let currentPage = 1;

const cardsPerPage = 6;


// ==================================================
// DEFAULT RECOMMENDED DAYS
// ==================================================

const DEFAULT_DAYS = {
    "Goa": 3,
    "Manali": 4,
    "Jaipur": 3,
    "Kerala Backwaters": 4,
    "Agra": 2,
    "Hampi": 3,
    "Amritsar": 2,
    "Rishikesh": 3,
    "Ladakh": 5,
    "Meghalaya": 4
};


// ==================================================
// IMAGE OVERRIDES
// ==================================================

const IMAGE_OVERRIDES = {
    "Manali":
        "https://www.sostravelhouse.com/public/uploads/images/post/67fe2ee9cc351.webp",

    "Hampi":
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Hampi_virupaksha_temple.jpg"
};


// ==================================================
// GET RECOMMENDED DAYS
// ==================================================

function getRecommendedDays(destination) {

    const apiDays = Number(
        destination.recommended_days ??
        destination.days ??
        destination.duration ??
        destination.number_of_days ??
        0
    );

    return apiDays > 0
        ? apiDays
        : (DEFAULT_DAYS[destination.name] || 0);
}


// ==================================================
// FILTERED DESTINATIONS
// ==================================================

let filteredDestinations = [];


// ==================================================
// LOAD DESTINATIONS FROM BACKEND
// ==================================================

async function loadDestinations() {

    try {

        const response = await fetch(
            `${API_URL}/api/destinations`
        );

        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }

        const result = await response.json();


        // Flask API can return:
        // [ ... ]
        // OR
        // { destinations: [ ... ] }
        // OR
        // { data: [ ... ] }

        const apiData =
            Array.isArray(result)
                ? result
                : (
                    result.destinations ||
                    result.data ||
                    []
                );


        // ==================================================
        // CONVERT BACKEND DATA
        // ==================================================

        destinations = apiData.map(
            function(destination) {

                return {

                    id:
                        destination.id ??
                        destination.destination_id,


                    name:
                        destination.name ??
                        destination.destination_name ??
                        "",


                    type:
                        destination.destination_type ??
                        destination.type ??
                        "",


                    description:
                        destination.description ??
                        "",


                    // Use budget_min from backend
                    budget:
                        Number(
                            destination.budget_min ??
                            destination.budget ??
                            destination.price ??
                            0
                        ),


                    budget_min:
                        Number(
                            destination.budget_min ??
                            0
                        ),


                    budget_max:
                        Number(
                            destination.budget_max ??
                            0
                        ),


                    // IMPORTANT:
                    // Use recommended days function
                    days:
                        getRecommendedDays(
                            destination
                        ),


                    rating:
                        Number(
                            destination.rating ??
                            0
                        ),


                    // IMPORTANT:
                    // First use image override,
                    // then backend image
                    image:
                        IMAGE_OVERRIDES[
                            destination.name
                        ] ||
                        destination.image_url ||
                        destination.image ||
                        destination.imageUrl ||
                        ""

                };

            }
        );


        // ==================================================
        // INITIAL DESTINATION LIST
        // ==================================================

        filteredDestinations =
            [...destinations];


        currentPage = 1;


        displayDestinations();


        console.log(
            "Destinations loaded from backend:",
            destinations
        );

    }

    catch (error) {

        console.error(
            "Error loading destinations:",
            error
        );


        const grid =
            document.getElementById(
                "destinationGrid"
            );


        if (grid) {

            grid.innerHTML = `
                <p style="
                    text-align:center;
                    width:100%;
                    padding:30px;
                ">
                    Unable to load destinations.
                    Please make sure the backend is running.
                </p>
            `;

        }

    }

}


// ==================================================
// DISPLAY DESTINATIONS
// ==================================================

function displayDestinations() {

    const grid =
        document.getElementById(
            "destinationGrid"
        );


    const noResults =
        document.getElementById(
            "noResults"
        );


    if (!grid) {

        console.error(
            "destinationGrid not found in HTML"
        );

        return;

    }


    // Clear old cards
    grid.innerHTML = "";


    const startIndex =
        (currentPage - 1) *
        cardsPerPage;


    const endIndex =
        startIndex +
        cardsPerPage;


    const pageDestinations =
        filteredDestinations.slice(
            startIndex,
            endIndex
        );


    // ==================================================
    // NO RESULTS
    // ==================================================

    if (
        pageDestinations.length === 0
    ) {

        if (noResults) {

            noResults.style.display =
                "block";

        }

        displayPagination();

        return;

    }


    if (noResults) {

        noResults.style.display =
            "none";

    }


    // ==================================================
    // CREATE DESTINATION CARDS
    // ==================================================

    pageDestinations.forEach(
        function(destination) {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "destination-card";


            card.innerHTML = `

                <img
                    src="${destination.image}"
                    alt="${destination.name}"
                    onerror="this.style.display='none';"
                >

                <div class="destination-card-content">

                    <h3>
                        ${destination.name}
                    </h3>

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


            // ==================================================
            // DESTINATION CLICK
            // ==================================================

            card.addEventListener(
                "click",
                async function() {


                    // ------------------------------------------
                    // SAVE SELECTED DESTINATION
                    // ------------------------------------------

                    localStorage.setItem(
                        "selectedDestination",
                        JSON.stringify(
                            destination
                        )
                    );


                    // Remember that destination
                    // was opened from Explore

                    localStorage.setItem(
                        "destinationSource",
                        "explore"
                    );


                    // ------------------------------------------
                    // RECORD INTERACTION
                    // ------------------------------------------

                    if (destination.id) {

                        try {

                            const response =
                                await fetch(
                                    `${API_URL}/api/destinations/${destination.id}/interaction`,
                                    {
                                        method: "POST",

                                        headers: {
                                            "Content-Type":
                                                "application/json"
                                        },

                                        body:
                                            JSON.stringify({
                                                interaction_type:
                                                    "click"
                                            })
                                    }
                                );


                            const result =
                                await response.json();


                            console.log(
                                "RAW BACKEND DATA:",
                                result
                            );


                            console.log(
                                "Interaction recorded:",
                                result
                            );

                        }

                        catch (error) {

                            console.error(
                                "Interaction error:",
                                error
                            );

                        }

                    }


                    // ------------------------------------------
                    // OPEN DESTINATION PAGE
                    // ------------------------------------------

                    window.location.href =
                        "destination.html";

                }
            );


            grid.appendChild(
                card
            );

        }
    );


    displayPagination();

}


// ==================================================
// PAGINATION
// ==================================================

function displayPagination() {

    const pagination =
        document.getElementById(
            "pagination"
        );


    if (!pagination) {

        return;

    }


    pagination.innerHTML = "";


    const totalPages =
        Math.ceil(
            filteredDestinations.length /
            cardsPerPage
        );


    if (totalPages <= 1) {

        return;

    }


    // ==================================================
    // PAGE NUMBERS
    // ==================================================

    for (
        let i = 1;
        i <= totalPages;
        i++
    ) {

        const button =
            document.createElement(
                "button"
            );


        button.textContent =
            i;


        if (i === currentPage) {

            button.classList.add(
                "active-page"
            );

        }


        button.onclick =
            function() {

                currentPage =
                    i;


                displayDestinations();


                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

            };


        pagination.appendChild(
            button
        );

    }


    // ==================================================
    // NEXT BUTTON
    // ==================================================

    if (
        currentPage < totalPages
    ) {

        const nextButton =
            document.createElement(
                "button"
            );


        nextButton.textContent =
            "›";


        nextButton.onclick =
            function() {

                currentPage++;


                displayDestinations();


                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

            };


        pagination.appendChild(
            nextButton
        );

    }

}


// ==================================================
// SEARCH
// ==================================================

function searchDestinations() {

    applyFilters();

}


// ==================================================
// FILTERS
// ==================================================

function applyFilters() {

    const searchElement =
        document.getElementById(
            "searchInput"
        );


    const typeElement =
        document.getElementById(
            "typeFilter"
        );


    const budgetElement =
        document.getElementById(
            "budgetFilter"
        );


    const durationElement =
        document.getElementById(
            "durationFilter"
        );


    const sortElement =
        document.getElementById(
            "sortFilter"
        );


    const searchValue =
        searchElement
            ? searchElement.value
                .toLowerCase()
                .trim()
            : "";


    const selectedType =
        typeElement
            ? typeElement.value
            : "all";


    const selectedBudget =
        budgetElement
            ? budgetElement.value
            : "all";


    const selectedDuration =
        durationElement
            ? durationElement.value
            : "all";


    const selectedSort =
        sortElement
            ? sortElement.value
            : "default";


    // ==================================================
    // FILTER DESTINATIONS
    // ==================================================

    filteredDestinations =
        destinations.filter(
            function(destination) {


                // ------------------------------------------
                // SEARCH
                // ------------------------------------------

                const matchesSearch =
                    destination.name
                        .toLowerCase()
                        .includes(
                            searchValue
                        );


                // ------------------------------------------
                // TYPE
                // ------------------------------------------

                const matchesType =
                    selectedType === "all" ||
                    String(destination.type || "")
                        .trim()
                        .toLowerCase() ===
                    String(selectedType || "")
                        .trim()
                        .toLowerCase();


                // ------------------------------------------
                // BUDGET
                // ------------------------------------------

                const matchesBudget =
                    selectedBudget === "all" ||
                    destination.budget <=
                        Number(
                            selectedBudget
                        );


                // ------------------------------------------
                // DURATION
                // ------------------------------------------

                const matchesDuration =
                    selectedDuration === "all" ||
                    Number(destination.days) ===
                        Number(selectedDuration);


                return (
                    matchesSearch &&
                    matchesType &&
                    matchesBudget &&
                    matchesDuration
                );

            }
        );


    // ==================================================
    // SORTING
    // ==================================================

    if (
        selectedSort === "priceLow"
    ) {

        filteredDestinations.sort(
            function(a, b) {

                return (
                    a.budget -
                    b.budget
                );

            }
        );

    }


    if (
        selectedSort === "priceHigh"
    ) {

        filteredDestinations.sort(
            function(a, b) {

                return (
                    b.budget -
                    a.budget
                );

            }
        );

    }


    if (
        selectedSort === "ratingHigh"
    ) {

        filteredDestinations.sort(
            function(a, b) {

                return (
                    b.rating -
                    a.rating
                );

            }
        );

    }


    // ==================================================
    // GO BACK TO PAGE 1
    // ==================================================

    currentPage = 1;


    displayDestinations();

}


// ==================================================
// PAGE LOAD
// ==================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {


        // ------------------------------------------
        // SEARCH ENTER KEY
        // ------------------------------------------

        const searchInput =
            document.getElementById(
                "searchInput"
            );


        if (searchInput) {

            searchInput.addEventListener(
                "keydown",
                function(event) {

                    if (
                        event.key === "Enter"
                    ) {

                        searchDestinations();

                    }

                }
            );

        }


        // ------------------------------------------
        // BACK TO EXPLORE BUTTON
        // ------------------------------------------

        const backToExplore =
            document.getElementById(
                "backToExplore"
            );


        if (backToExplore) {

            backToExplore.addEventListener(
                "click",
                function() {

                    window.location.href =
                        "explore.html";

                }
            );

        }


        // ------------------------------------------
        // LOAD DESTINATIONS
        // ------------------------------------------

        loadDestinations();

    }
);