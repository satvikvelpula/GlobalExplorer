let map = L.map('map', {
    worldCopyJump: true,
    continuousWorld: true,
    minZoom: 3,
    maxZoom: 18
}).setView([0, 0], 2);


L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: "",
    noWrap: false
}).addTo(map);

map.setMaxBounds([
    [-90, -Infinity],
    [90, Infinity]
]);



const fullscreenBtn = document.getElementById('fullscreenBtn');
const closeFullscreenBtn = document.getElementById('closeFullscreenBtn');
const gameMapContainer = document.querySelector('.game-map-container');

const overModal = document.querySelector('.overmodal');
const overModal_h2 = document.querySelector('.overModal-h2');
const overModal_p = document.querySelector('.overModal-p');

fullscreenBtn.addEventListener('click', function () {
    gameMapContainer.classList.toggle('fullscreen');

    if (gameMapContainer.classList.contains('fullscreen')) {
        closeFullscreenBtn.style.display = "inline-block";
        fullscreenBtn.classList.remove('fa-expand');
        fullscreenBtn.classList.add('fa-compress');
    } else {
        closeFullscreenBtn.style.display = "none";
        fullscreenBtn.classList.remove('fa-compress');
        fullscreenBtn.classList.add('fa-expand');
    }
});

closeFullscreenBtn.addEventListener('click', function () {

    closeFullscreenBtn.style.display = "none";
    gameMapContainer.classList.remove('fullscreen');

    fullscreenBtn.classList.remove('fa-compress');
    fullscreenBtn.classList.add('fa-expand');
});



let markers = {};

const dynamicContainer = document.querySelector("#dynamic-container");
const currentAirportText = document.querySelector(".current-airport-h3");

let markersLayer = L.layerGroup().addTo(map);
let markersMap = {};

let countryMarkersMap = {};

let visitedCountries = [];

let countryTest = "";
let selectedCountry = "";

function sanitizeId(id) {
    return id.replace(/[^\w-]/g, '-');
}

let isCheckingGameStatus = false;

function updateIcao(icao) {
    const icao_code = icao;  // ICAO code entered by user

    const toast = document.querySelector(".toast");
    const toast_text = document.querySelector(".text-2");
    const closeIcon = document.querySelector(".close");
    const progress = document.querySelector(".progress");
    let timer1, timer2;

    fetch('http://127.0.0.1:5000/icao', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({icao_code: icao_code})
    })
    .then(response => response.json())
    .then(responseData => {
        const flightsRemaining = responseData.flights_remaining;
        const completedGoals = responseData.completed_goals;

        if (completedGoals.length === 4) {
            console.log("You have won the game, since you have completed all the goals!");
            overModal.style.display = "block";
            overModal_h2.innerHTML = "You Win! 🏆";
            overModal_p.innerHTML = "Congratulations! You have completed all the goals in less than 30 flights remaining. Well done!";

        } else if (flightsRemaining === 0) {
            console.log("Flights remaining is zero, and you have not completed all the goals. You lost!");
            overModal.style.display = "block";
            overModal_h2.innerHTML = "You Lose! 😞";
            overModal_p.innerHTML = "Unfortunately, you have exceeded the flight limit. You failed to complete all the goals within the remaining 30 flights. Better luck next time!";

        } else {
            console.log("Game is still ongoing.");
            overModal.style.display = "none";
        }

        document.querySelector(".username").innerHTML = `${responseData.username}`;
        document.querySelector(".countries-visited").innerHTML = `${responseData.visited_airports.length > 0 ? responseData.visited_airports.join(", ") : "None"}`;
        document.querySelector(".continents-visited").innerHTML = `${responseData.continents_visited.length > 0 ? responseData.continents_visited.join(", ") : "None"}`;
        document.querySelector(".completed-goals").innerHTML = `${responseData.completed_goals.length > 0 ? responseData.completed_goals.join(", ") : "None"}`;

        document.querySelector(".countries-visited-over").innerHTML = `${responseData.visited_airports.length > 0 ? responseData.visited_airports.join(", ") : "None"}`;
        document.querySelector(".continents-visited-over").innerHTML = `${responseData.continents_visited.length > 0 ? responseData.continents_visited.join(", ") : "None"}`;
        document.querySelector(".completed-goals-over").innerHTML = `${responseData.completed_goals.length > 0 ? responseData.completed_goals.join(", ") : "None"}`;


        const rewardSpan = document.querySelector(".reward");
        const rewardSpanOver = document.querySelector(".reward-over");

        let rewardHTML = "No rewards";
        let rewardStyle = "";

        let rewardHTMLOver = "No rewards";
        let rewardStyleOver = "";

        if (responseData.reward === "Bronze") {
            rewardHTML = "Bronze";
            rewardStyle = "background-color: #cd7f32; color: white; border-radius: 5px; padding: 2px 5px;";
            rewardHTMLOver = "Bronze";
            rewardStyleOver = "background-color: #cd7f32; color: white; border-radius: 5px; padding: 2px 5px;";
        } else if (responseData.reward === "Silver") {
            rewardHTML = "Silver";
            rewardStyle = "background-color: #c0c0c0; color: black; border-radius: 5px; padding: 2px 5px;";
            rewardHTMLOver = "Silver";
            rewardStyleOver = "background-color: #c0c0c0; color: black; border-radius: 5px; padding: 2px 5px;";
        } else if (responseData.reward === "Gold") {
            rewardHTML = "Gold";
            rewardStyle = "background-color: #ffd700; color: white; border-radius: 5px; padding: 2px 5px;";
            rewardHTMLOver = "Gold";
            rewardStyleOver = "background-color: #ffd700; color: black; border-radius: 5px; padding: 2px 5px;";
        } else if (responseData.reward === "Platinum") {
            rewardHTML = "Platinum";
            rewardStyle = "background-color: #b9f2ff; color: black; border-radius: 5px; padding: 2px 5px;";
            rewardHTMLOver = "Platinum";
            rewardStyleOver = "background-color: #b9f2ff; color: black; border-radius: 5px; padding: 2px 5px;";
        }


        rewardSpan.innerHTML = `
          <strong><i class="fas fa-gift" style="margin-right: 10px; margin-top: 10px"></i> Reward:</strong>
          <span style="${rewardStyle}">${rewardHTML}</span>
        `;

        rewardSpanOver.innerHTML = `
          <strong><i class="fas fa-gift" style="margin-right: 10px; margin-top: 10px"></i> Reward:</strong>
          <span style="${rewardStyleOver}">${rewardHTMLOver}</span>
        `;


        document.querySelector(".last-airport").innerHTML = `${responseData.last_airport}`;
        document.querySelector(".last-airport-over").innerHTML = `${responseData.last_airport}`;
        document.querySelector(".flights-remaining").innerHTML = `${responseData.flights_remaining}`;
        document.querySelector(".flights-remaining-over").innerHTML = `${responseData.flights_remaining}`;
        document.querySelector(".flights_remaining_side_span").innerHTML = `${responseData.flights_remaining}`;

        if (responseData.completed_goals && responseData.completed_goals.length === 4) {
            console.log("Completed goals:", responseData.completed_goals);
        }
        const newGoals = responseData.completed_goals;
        if (Array.isArray(newGoals)) {
            const previousGoals = responseData.previous_goals || [];
            const addedGoals = newGoals.filter(goal => !previousGoals.includes(goal));

            addedGoals.forEach(goal => {
                console.log('New goal completed:', goal);

                // Toast notification
                toast.classList.add("active");
                progress.classList.add("active");
                toast_text.innerHTML = goal;

                timer1 = setTimeout(() => {
                    toast.classList.remove("active");
                }, 5000);

                timer2 = setTimeout(() => {
                    progress.classList.remove("active");
                }, 5300);

                closeIcon.addEventListener("click", () => {
                    toast.classList.remove("active");
                    setTimeout(() => {
                        progress.classList.remove("active");
                    }, 300);
                    clearTimeout(timer1);
                    clearTimeout(timer2);
                });

                const goalName = goal;
                const goalElement = document.getElementById(`goal-${goalName.replace(/\s+/g, '-')}`);
                if (goalElement) {
                    const goalStatusSpan = goalElement.querySelector('.goal-status');
                    if (goalStatusSpan) {
                        goalStatusSpan.style.backgroundColor = 'green';
                        goalStatusSpan.style.color = 'white';
                        goalStatusSpan.style.borderColor = 'darkgreen';
                        goalStatusSpan.innerHTML = `Completed <i class="fa fa-check" style="margin-left: 5px;"></i>`;
                    }
                }
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}



function fetchNearbyCountries(icao) {
    restoreMarkers();
    dynamicContainer.innerHTML = `
        <div class="parent-container">
              <div class="wrapper-loading">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
        </div>
    `;

    fetch("/get_nearby_countries", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ icao: icao }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then((data) => {
            dynamicContainer.innerHTML = "";

            if (data.length === 0) {
                dynamicContainer.innerHTML = "<p>No nearby countries found.</p>";
                return;
            }

            const title = document.createElement("h3");
            title.innerText = "Nearby countries:";
            dynamicContainer.appendChild(title);

            const countryMarkers = [];
            const countryMarkersMap = {};

            data.forEach((countryData, index) => {
                const button = document.createElement("button");
                button.classList.add("side-buttons");
                button.innerHTML = `${index + 1}. ${countryData.country} (<span>${countryData.continent}</span>) - ${countryData.distance.toFixed(2)} km`;

                button.dataset.country = countryData.country;

                button.addEventListener("click", () => {
                    fetchAirports(countryData.country);
                    countryMarkers.forEach((m) => {
                        map.removeLayer(m);
                    });
                });

                dynamicContainer.appendChild(button);

                button.addEventListener("mouseover", () => {
                    const marker = countryMarkersMap[countryData.country];
                    if (marker) {
                        const { lat, lng } = marker.getLatLng();
                        map.setView([lat, lng], 6, { animate: true });
                        marker.openTooltip();
                    }
                });

                button.addEventListener("mouseout", () => {
                    const marker = countryMarkersMap[countryData.country];
                    if (marker) {
                        marker.closeTooltip();
                    }
                });

                if (countryData.coordinates && countryData.coordinates.length === 2) {
                    const [lat, lng] = countryData.coordinates;
                    const marker = L.marker([lat, lng], { icon: redIcon });

                    marker.bindTooltip(
                        `<b>${countryData.country}</b>`,
                        {
                            permanent: false,
                            direction: "top",
                            offset: [0, -41],
                        }
                    );


                    const sanitizedCountryName = sanitizeId(countryData.country);
                    const travelButtonId = `travel-button-${sanitizedCountryName}`;
                    const travelButton = `<button class="travel-button" id="${travelButtonId}">
                        Travel Country
                    </button>`;

                    marker.bindPopup(`
                        <img src="https://flagsapi.com/${countryData.iso_country}/flat/64.png" 
                             alt="${countryData.country} flag" 
                             style="display: block; margin: 0 auto 10px; width: 80px; height: auto;" 
                             onerror="this.style.display='none';">
                        <strong>${countryData.country}</strong><br>
                        Distance: ${countryData.distance.toFixed(2)} km<br>
                        ${travelButton}
                    `);




                    marker.addTo(map);
                    countryMarkers.push(marker);
                    countryMarkersMap[countryData.country] = marker; // Map country to marker

                    marker.on('popupopen', () => {
                        const popupButton = document.querySelector(`#${travelButtonId}`);
                        if (popupButton) {
                            popupButton.addEventListener("click", () => {
                                fetchAirports(countryData.country);
                                countryMarkers.forEach((m) => {
                                    map.removeLayer(m);
                                });
                                marker.closePopup();
                            });
                        }
                    });
                }
            });

            dimOtherMarkers(icao);
        })
        .catch((error) => {
            console.error("Error fetching nearby countries:", error);
            dynamicContainer.innerHTML = "<p>Error fetching nearby countries.</p>";
        });
}

function fetchAirports(country) {
    selectedCountry = country;
    if (markers["markerLastAirport"]) {
        markers["markerLastAirport"].remove();
    }
    restoreMarkers();

    dynamicContainer.innerHTML = `
        <div class="parent-container">
              <div class="wrapper-loading">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
        </div>
    `;

    fetch("/get_airports_in_country", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ country: country }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then((data) => {
            dynamicContainer.innerHTML = ""; // Clear the container
            if (data.length === 0) {
                dynamicContainer.innerHTML = "<p>No airports found in this country.</p>";
                return;
            }


            const title = document.createElement("h3");
            title.innerText = `Airports in ${country} (${data.length} airports)`;
            dynamicContainer.appendChild(title);

            // Display airport buttons
            data.forEach((airport, index) => {
                const button = document.createElement("button");
                button.classList.add("side-buttons");
                button.innerHTML = `${index + 1}. ${airport.name} (${airport.icao})`;

                button.addEventListener("click", () => {
                    document.querySelector("#starting-airport").style.display = "none";
                    fetchNearbyCountries(airport.icao)
                    checkGameStatus();
                    updateIcao(airport.icao)

                    currentAirportText.innerHTML = `Current airport: ${airport.name} (${airport.icao}) - ${selectedCountry}`;
                });

                button.addEventListener("mouseover", () => {
                    highlightMarkerWithTooltip(airport.icao);

                    // Pan to marker location
                    const marker = markersMap[airport.icao];

                    if (marker) {
                        const { lat, lng } = marker.getLatLng();
                        map.setView([lat, lng], 6, { animate: true }); // Adjust zoom level if necessary
                    }
                });

                button.addEventListener("mouseout", () => {
                    resetMarker(airport.icao);
                });

                dynamicContainer.appendChild(button);
            });

            addAirportsToMap(data);


        })
        .catch((error) => {
            console.error("Error fetching airports:", error);
            dynamicContainer.innerHTML = "<p>Error fetching airports.</p>";
        });
}


function addAirportsToMap(airports) {
    markersLayer.clearLayers(); // Clear existing markers
    markersMap = {}; // Reset the markers map

    airports.forEach((airport) => {
        const { icao, name, latitude_deg, longitude_deg } = airport;
        if (latitude_deg && longitude_deg) {
            const marker = L.marker([latitude_deg, longitude_deg], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                    iconSize: [25, 41], // Default size of Leaflet markers
                    iconAnchor: [12.5, 41], // Anchor at the bottom center of the icon
                })
            }).addTo(markersLayer);

            // Store marker reference in the markers map
            markersMap[icao] = marker;

            map.setView([latitude_deg, longitude_deg], 3);

            marker.bindTooltip(`
                <b>${name} (${icao})</b><br>
            `, {
                permanent: false,
                direction: "top", // Position above the marker
                offset: [0, -41], // Move tooltip upwards to clear the marker (same as icon height)
            });

            marker.bindPopup(`
            <b>${name} (${icao})</b><br>
            <button class="travel-button" id="airport-${icao}-popup-button">Visit Airport</button>`, {
                permanent: false,
                direction: "top", // Position above the marker
                offset: [0, -41], // Move tooltip upwards to clear the marker (same as icon height)
            });

            // Add event listener to the popup button
            marker.on('popupopen', function () {
                const popupButton = document.querySelector(`#airport-${icao}-popup-button`);
                if (popupButton) {
                    popupButton.addEventListener("click", () => {
                        handleAirportButtonClick(icao);
                        checkGameStatus();
                        currentAirportText.textContent = `Current airport: ${airport.name} (${airport.icao}) - ${selectedCountry}`;
                        marker.closePopup();
                        marker.unbindPopup();
                    });
                }
            });
            marker.on("mouseover", () => marker.openTooltip());
            marker.on("mouseout", () => marker.closeTooltip());
        }
    });
}

function handleAirportButtonClick(icao) {
    document.querySelector("#starting-airport").style.display = "none";
    locationSelected = true;
    console.log("Location selected: ", locationSelected);
    fetchNearbyCountries(icao);
    updateIcao(icao)
    if (markers["markerLastAirport"]) {
        markers["markerLastAirport"].remove();
    }
    console.log("Airport button is clicked function: handleAirportButtonClick.");
}



function highlightMarkerWithTooltip(icao) {
    const marker = markersMap[icao];

    if (marker) {
        marker.openTooltip();

        marker.setIcon(
            L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                iconSize: [35, 51], // Larger size for highlight
                iconAnchor: [17.5, 51], // Adjust anchor for larger size
            })
        );
    }
}

function resetMarker(icao) {
    const marker = markersMap[icao];
    if (marker) {
        marker.closeTooltip(); // Programmatically close the tooltip

        // Reset the marker style
        marker.setIcon(
            L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                iconSize: [25, 41], // Default size
                iconAnchor: [12.5, 41], // Default anchor
            })
        );
    }
}

const defaultIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var violetIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

function dimOtherMarkers(selectedIcao) {
    Object.keys(markersMap).forEach((icao) => {
        const marker = markersMap[icao];
        if (icao !== selectedIcao) {
            markersLayer.removeLayer(marker); // Remove non-selected markers
        }
    });
}

function restoreMarkers() {
    Object.keys(markersMap).forEach((icao) => {
        const marker = markersMap[icao];
        //console.log(marker);
        if (!markersLayer.hasLayer(marker)) {
            markersLayer.addLayer(marker); // Add back any markers removed from the map
        }
        marker.setIcon(defaultIcon)
        marker.setOpacity(1); // Ensure all markers are fully visible
        marker.closePopup();
        marker.unbindPopup();

       marker.bindTooltip(`
            <b>Current airport: ${icao}</b><br>
        `, {
            permanent: false,
            direction: "top", // Position above the marker
            offset: [0, -41], // Move tooltip upwards to clear the marker (same as icon height)
        });
    });
}


document.querySelector("#fetch-nearby-countries").addEventListener("click", () => {
    const icaoInput = document.querySelector("#current-airport-input").value.trim();

    if (!icaoInput) {
        alert("Please enter a valid ICAO code.");
        return;
    }

    fetchNearbyCountries(icaoInput);
});


document.addEventListener("DOMContentLoaded", function () {
    // Fetch the visited country coordinates from the server
    fetch("/get_visited_country_coordinates")
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error fetching visited country coordinates:", data.error);
                return;
            }

            data.forEach(country => {
                const { country: countryName, latitude, longitude } = country;

                const visitedCountries = data.map(country => country.country); // assuming 'country' is the country name

            });

            const bounds = data.map(country => [country.latitude, country.longitude]);
            map.fitBounds(bounds);
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
});


function getLastAirport() {
    fetch("/get_last_airport")
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error); // Handle the error
            } else if (data) {
                const lastAirport = data.last_airport;
                const latitude = data.latitude_deg;
                const longitude = data.longitude_deg;
                const countryName = data.country;
                const name = data.name;
                const flightsRemaining = data.flights_remaining;
                const completedGoals = data.goals_completed || [];
                const totalGoals = 4;

                // Check if a last airport exists
                if (lastAirport) {
                    document.querySelector("#starting-airport").style.display = "none";

                    const currentAirportText = document.querySelector(".current-airport-h3");
                    currentAirportText.textContent = `Current airport: ${name} (${lastAirport}) - ${countryName}`;

                    // Add a marker for the last airport on the map
                    if (!markers["markerLastAirport"]) { // Prevent duplicate markers
                        const markerLastAirport = L.marker([latitude, longitude]).addTo(map);
                        markerLastAirport.setIcon(defaultIcon); // Use default icon
                        markerLastAirport.unbindPopup();
                        markerLastAirport.bindTooltip(`
                            <b>Current airport: ${name}</b><br>
                        `, {
                            permanent: false,
                            direction: "top",
                            offset: [0, -41],
                        });

                        // Store the marker for potential removal or updates
                        markers["markerLastAirport"] = markerLastAirport;
                    }

                    // Fetch nearby countries
                    fetchNearbyCountries(lastAirport);
                    //triggerGameStatusCheck()


                } else {
                    // Show the input box for the user to enter a new ICAO code
                    document.querySelector("#starting-airport").style.display = "block";
                }
            }
        })
        .catch(error => console.error("Error fetching last airport data:", error));
}


getLastAirport();




function checkGameStatus() {
    fetch("/get_game_status")
        .then(response => response.json())
        .then(data => {
            const flightsRemaining = data.flights_remaining;
            const completedGoals = data.completed_goals;

            if (data.error) {
                console.error(data.error); // Handle the error
            } else {

                if (completedGoals.length === 4) {
                    console.log("You have won the game, since you have completed all the goals!");
                    overModal.style.display = "block";
                    overModal_h2.innerHTML = "You Win! 🏆";
                    overModal_p.innerHTML = "Congratulations! You have completed all the goals in less than 30 flights remaining. Well done!";
                    dynamicContainer.parentNode.removeChild(dynamicContainer);
                    dynamicContainer.style.display = "none";
                } else if (flightsRemaining === 0) {
                    console.log("Flights remaining is zero, and you have not completed all the goals. You lost!");
                    overModal.style.display = "block";
                    overModal_h2.innerHTML = "You Lose! 😞";
                    overModal_p.innerHTML = "Unfortunately, you have exceeded the flight limit. You failed to complete all the goals within the remaining 30 flights. Better luck next time!";
                    dynamicContainer.style.display = "none";
                    dynamicContainer.parentNode.removeChild(dynamicContainer);
                } else {
                    console.log("Game is still ongoing.");
                    overModal.style.display = "none";
                }
            }

        })
        .catch(error => console.error("Error fetching game status:", error));
}

checkGameStatus();
