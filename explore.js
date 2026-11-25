
const API_URL = "http://127.0.0.1:5000";

let destinations = [];
let filteredDestinations = [];
let currentPage = 1;

const cardsPerPage = 6;

// --------------------------------------------------
// HTML SAFETY
// --------------------------------------------------

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

// --------------------------------------------------
// FORMAT BUDGET
// --------------------------------------------------

function formatBudget(value) {
    const amount = Number(value);

    if (!Number.isFinite(amount)) {
        return "Not specified";
    }

    return "₹" + amount.toLocaleString("en-IN", {
        maximumFractionDigits: 0
    });
}

// --------------------------------------------------
// LOAD DESTINATIONS FROM MYSQL THROUGH FLASK
// --------------------------------------------------

async function loadDestinations() {
    const grid = document.getElementById("destinationGrid");

    if (!grid) return;

    grid.innerHTML = "<p>Loading destinations...</p>";

    try {
        const response = await fetch(`${API_URL}/api/destinations`);

        if (!response.ok) {
            throw new Error("Unable to fetch destinations.");
        }

        const result = await response.json();

        const records = Array.isArray(result)
            ? result
            : result.destinations || result.data || [];

        destinations = records.map(destination => ({
            ...destination,

            id: destination.id ?? destination.destination_id,
            name: destination.name ?? destination.destination_name ?? "Unknown destination",
            type: destination.destination_type ?? destination.type ?? "Other",

            description: destination.description || "",

            budget_min: destination.budget_min == null
                ? NaN
                : Number(destination.budget_min),

            budget_max: destination.budget_max == null
                ? NaN
                : Number(destination.budget_max),

            days: Number(
                destination.recommended_days ??
                destination.days ??
                0
            ),

            rating: Number(destination.rating ?? 0),

            image: String(
                destination.image_url || destination.image || ""
            ).trim()
        }));

        filteredDestinations = [...destinations];

populateFilters();

// RESTORE FILTERED RESULTS IF RETURNING FROM DESTINATION DETAILS
if (!restoreExploreState()) {

    currentPage = 1;
    filteredDestinations = [...destinations];

    displayDestinations();
}
    } catch (error) {
        console.error("Destination loading error:", error);

        grid.innerHTML = `
            <p class="no-results" style="display:block;">
                Unable to load destinations.
                Please check whether the backend is running.
            </p>
        `;
    }
}

// --------------------------------------------------
// POPULATE FILTERS USING DATABASE VALUES
// --------------------------------------------------


function populateFilters() {

    // CATEGORY FILTER - USE DATABASE CATEGORIES

    const typeFilter = document.getElementById("typeFilter");

    if (typeFilter) {
        const selectedType = typeFilter.value;

        const categories = [
            ...new Set(
                destinations
                    .map(destination => destination.type)
                    .filter(Boolean)
            )
        ].sort();

        typeFilter.innerHTML = `
            <option value="">All Categories</option>
            ${categories.map(category => `
                <option value="${escapeHTML(category)}">
                    ${escapeHTML(category)}
                </option>
            `).join("")}
        `;

        typeFilter.value = categories.includes(selectedType)
            ? selectedType
            : "";
    }

    // BUDGET FILTER - USE MINIMUM AND MAXIMUM DATABASE BUDGETS

    const budgetFilter = document.getElementById("budgetFilter");

    if (budgetFilter) {
        const selectedBudget = budgetFilter.value;

        const allBudgets = destinations.flatMap(destination => [
            Number(destination.budget_min),
            Number(destination.budget_max)
        ]).filter(amount =>
            Number.isFinite(amount) && amount > 0
        );

        const highestBudget = allBudgets.length
            ? Math.max(...allBudgets)
            : 0;

        const highestLimit = Math.ceil(highestBudget / 5000) * 5000;

        const budgetOptions = [];

        for (let amount = 5000; amount <= highestLimit; amount += 5000) {
            budgetOptions.push(amount);
        }

        budgetFilter.innerHTML = `
            <option value="">All Budgets</option>
            ${budgetOptions.map(amount => `
                <option value="${amount}">
                    Up to ${formatBudget(amount)}
                </option>
            `).join("")}
        `;

        budgetFilter.value = budgetOptions.includes(Number(selectedBudget))
            ? selectedBudget
            : "";
    }

    // DURATION FILTER - USE DATABASE DURATIONS

    const durationFilter = document.getElementById("durationFilter");

    if (durationFilter) {
        const selectedDays = durationFilter.value;

        const durations = [
            ...new Set(
                destinations
                    .map(destination => destination.days)
                    .filter(days => Number.isFinite(days) && days > 0)
            )
        ].sort((a, b) => a - b);

        durationFilter.innerHTML = `
            <option value="">Any Duration</option>
            ${durations.map(days => `
                <option value="${days}">
                    ${days} Days
                </option>
            `).join("")}
        `;

        durationFilter.value = durations.includes(Number(selectedDays))
            ? selectedDays
            : "";
    }
}


// --------------------------------------------------
// DISPLAY DESTINATION CARDS
// --------------------------------------------------

function displayDestinations() {

    const grid = document.getElementById("destinationGrid");
    const noResults = document.getElementById("noResults");
    const pagination = document.getElementById("pagination");

    if (!grid) return;

    const totalPages = Math.ceil(
        filteredDestinations.length / cardsPerPage
    );

    if (filteredDestinations.length === 0) {
        grid.innerHTML = "";

        if (noResults) {
            noResults.style.display = "block";
        }

        if (pagination) {
            pagination.innerHTML = "";
        }

        return;
    }

    if (noResults) {
        noResults.style.display = "none";
    }

    const startIndex = (currentPage - 1) * cardsPerPage;

    const pageDestinations = filteredDestinations.slice(
        startIndex,
        startIndex + cardsPerPage
    );

    grid.innerHTML = pageDestinations.map(destination => {

        const imageHTML = destination.image
            ? `
                <div class="destination-image-wrap">
                    <img
                        src="${escapeHTML(destination.image)}"
                        alt="${escapeHTML(destination.name)}"
                        class="destination-card-image"
                        loading="lazy"
                    >
                    <div class="destination-image-fallback" hidden>
                        Image unavailable
                    </div>
                </div>
            `
            : `
                <div class="destination-image-wrap">
                    <div class="destination-image-fallback">
                        Image unavailable
                    </div>
                </div>
            `;

        const budgetText =
    Number.isFinite(destination.budget_min) &&
    Number.isFinite(destination.budget_max)
        ? `${formatBudget(destination.budget_min)} - ${formatBudget(destination.budget_max)}`
        : "Budget information currently unavailable";

        const durationText =
            destination.days > 0
                ? `${destination.days} Days`
                : "Duration not specified";

        return `
            <div class="explore-destination-card"
                 data-id="${escapeHTML(destination.id)}">

                ${imageHTML}

                <div class="destination-card-content">

    <h3>
        ${escapeHTML(destination.name)}
    </h3>

    <p class="destination-type">
        ${escapeHTML(destination.type)}
    </p>

                    <p class="destination-description">
                        ${escapeHTML(
                            destination.description ||
                            "Explore this beautiful destination."
                        )}
                    </p>

                    <div class="destination-info-row">
                        <span>${escapeHTML(budgetText)}</span>
                    </div>

                    <div class="destination-days">
                        ${escapeHTML(durationText)}
                    </div>

                </div>
            </div>
        `;

    }).join("");

    // HANDLE MISSING OR BROKEN IMAGES

    grid.querySelectorAll(".destination-card-image").forEach(image => {

        function showFallback() {
            image.style.display = "none";

            const fallback = image.nextElementSibling;

            if (fallback) {
                fallback.hidden = false;
            }
        }

        image.addEventListener("error", showFallback);

        if (image.complete && image.naturalWidth === 0) {
            showFallback();
        }
    });

    

   
    // OPEN DESTINATION DETAILS

    grid.querySelectorAll(".explore-destination-card").forEach(card => {

        card.addEventListener("click", async function () {

            const destinationId = Number(this.dataset.id);

            const selected = destinations.find(
                destination => Number(destination.id) === destinationId
            );

            if (!selected) return;

            // SAVE CURRENT FILTERS, SEARCH AND PAGE NUMBER
            const exploreState = {
                search: document.getElementById("searchInput")?.value || "",
                type: document.getElementById("typeFilter")?.value || "",
                budget: document.getElementById("budgetFilter")?.value || "",
                duration: document.getElementById("durationFilter")?.value || "",
                sort: document.getElementById("sortFilter")?.value || "",
                page: currentPage
            };

            sessionStorage.setItem(
                "waymateExploreState",
                JSON.stringify(exploreState)
            );

            // SAVE SELECTED DESTINATION
            localStorage.setItem(
                "selectedDestination",
                JSON.stringify(selected)
            );

            localStorage.setItem("destinationSource", "explore");

            // RECORD DESTINATION CLICK
            try {
                await fetch(
                    `${API_URL}/api/destinations/${destinationId}/interaction`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            interaction_type: "click"
                        })
                    }
                );
            } catch (error) {
                console.error("Interaction recording failed:", error);
            }

            // OPEN DESTINATION DETAILS
            window.location.href = "destination.html?source=explore";
        });

    });

    displayPagination(totalPages);
}

// --------------------------------------------------
// PAGINATION
// --------------------------------------------------

function displayPagination(totalPages) {

    const pagination = document.getElementById("pagination");

    if (!pagination) return;

    if (totalPages <= 1) {
        pagination.innerHTML = "";
        return;
    }

    let html = "";

    for (let page = 1; page <= totalPages; page++) {
        html += `
            <button
                class="${page === currentPage ? "active-page" : ""}"
                data-page="${page}">
                ${page}
            </button>
        `;
    }

    if (currentPage < totalPages) {
        html += `
            <button data-page="${currentPage + 1}">
                Next →
            </button>
        `;
    }

    pagination.innerHTML = html;

    pagination.querySelectorAll("button").forEach(button => {
        button.addEventListener("click", function () {
            currentPage = Number(this.dataset.page);
            displayDestinations();

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        });
    });
}

// --------------------------------------------------
// SEARCH AND FILTERS
// --------------------------------------------------

function applyFilters() {

    const searchInput = document.getElementById("searchInput");
    const typeFilter = document.getElementById("typeFilter");
    const budgetFilter = document.getElementById("budgetFilter");
    const durationFilter = document.getElementById("durationFilter");
    const sortFilter = document.getElementById("sortFilter");

    const searchText = searchInput
        ? searchInput.value.trim().toLowerCase()
        : "";

    const selectedType = typeFilter ? typeFilter.value : "";

    const selectedBudget = budgetFilter && budgetFilter.value
        ? Number(budgetFilter.value)
        : 0;

    const selectedDays = durationFilter && durationFilter.value
        ? Number(durationFilter.value)
        : 0;

    filteredDestinations = destinations.filter(destination => {

        const matchesSearch =
            String(destination.name).toLowerCase().includes(searchText) ||
            String(destination.location || "").toLowerCase().includes(searchText);

        const matchesType =
            !selectedType || destination.type === selectedType;

        const matchesBudget =
            !selectedBudget ||
            (Number.isFinite(destination.budget_min) &&
                destination.budget_min <= selectedBudget);

        const matchesDuration =
            !selectedDays ||
            destination.days === selectedDays;

        return (
            matchesSearch &&
            matchesType &&
            matchesBudget &&
            matchesDuration
        );
    });

    const sortValue = sortFilter ? sortFilter.value : "default";

    if (sortValue === "priceLow") {
        filteredDestinations.sort(
            (a, b) => a.budget_min - b.budget_min
        );
    } else if (sortValue === "priceHigh") {
        filteredDestinations.sort(
            (a, b) => b.budget_min - a.budget_min
        );
    } else if (sortValue === "ratingHigh") {
        filteredDestinations.sort(
            (a, b) => b.rating - a.rating
        );
    }

    currentPage = 1;
    displayDestinations();
}

// RESTORE FILTERED EXPLORE RESULTS AFTER RETURNING FROM DESTINATION

function restoreExploreState() {

    const savedState = sessionStorage.getItem("waymateExploreState");

    if (!savedState) {
        return false;
    }

    try {
        const state = JSON.parse(savedState);

        // RESTORE SEARCH
        document.getElementById("searchInput").value =
            state.search || "";

        // RESTORE FILTERS
        document.getElementById("typeFilter").value =
            state.type || "";

        document.getElementById("budgetFilter").value =
            state.budget || "";

        document.getElementById("durationFilter").value =
            state.duration || "";

        document.getElementById("sortFilter").value =
            state.sort || "";

        // APPLY THE PREVIOUS FILTERS
        applyFilters();

        // RESTORE PREVIOUS PAGE NUMBER
        const totalPages = Math.max(
            1,
            Math.ceil(filteredDestinations.length / cardsPerPage)
        );

        currentPage = Math.min(
            Math.max(1, Number(state.page) || 1),
            totalPages
        );

        displayDestinations();

        return true;

    } catch (error) {
        console.error("Explore state restoration failed:", error);

        sessionStorage.removeItem("waymateExploreState");

        return false;
    }
}

// --------------------------------------------------
// EVENT LISTENERS
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("searchInput");

    if (searchInput) {
        searchInput.addEventListener("input", applyFilters);
    }

    [
        "typeFilter",
        "budgetFilter",
        "durationFilter",
        "sortFilter"
    ].forEach(id => {

        const element = document.getElementById(id);

        if (element) {
            element.addEventListener("change", applyFilters);
        }

    });

    const backButton = document.getElementById("backToExplore");

    if (backButton) {
        backButton.addEventListener("click", function () {
            window.location.href = "explore.html";
        });
    }

    loadDestinations();
});
