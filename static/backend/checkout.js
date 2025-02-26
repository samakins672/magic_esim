$(document).ready(function () {
    const packageCode = $("#package_code").val();
    const locationCode = $("#location_code").val();
    const type = $("#type").val();
    const plan_type = $("#plan_type").val();

    const seller = plan_type === 'u' ? 'esimgo' : 'esimaccess';

    loader = $('.loading');
    loader.removeClass("d-none");

    if (seller === 'esimaccess') {
        // Fetch eSIM plans via AJAX
        $.ajax({
            url: '/api/esim/plans/', // API endpoint
            type: 'GET',
            data: { packageCode: packageCode },
            success: function (response) {
                if (response.status) {
                    // Filter and sort plans
                    const sortedPlans = response.data.standard
                        .sort((a, b) => a.price - b.price); // Sort by price (ascending)

                    const plan = sortedPlans[0];
                    const locationDetails = plan.locationNetworkList;
                    console.log(plan);

                    // Determine Plan Name
                    if (type == 'single') {
                        planImage = `https://flagcdn.com/w320/${plan.locationNetworkList[0].locationCode.toLowerCase()}.png`;
                        planName = plan.locationNetworkList[0].locationName;
                    } else {
                        const locationCount = plan.locationNetworkList.length;
                        if (type == 'region') {
                            planImage = `/static/img/regions/${locationCode.toLowerCase()}.png`;
                        } else {
                            planImage = `/static/img/regions/as.png`;
                        }
                        planName = locationCount > 1 ? `${locationCount} Countries` : `${locationCount} Country`;
                    }

                    // Determine Plan Type
                    const planType = plan.smsStatus === 1 ? "Data and SMS" : "Data Only";

                    // Generate Supported Countries List
                    const supportedCountriesList = locationDetails
                        .map(
                            (location) => `
                            <div class="oneSupportedCountry">
                                <img src="https://flagcdn.com/w320/${location.locationCode.toLowerCase()}.png" alt="">
                                <h1>${location.locationName}</h1>
                            </div>
                        `
                        )
                        .join("");


                    const networkGroups = {};

                    // Iterate through all locations and their operators
                    locationDetails.forEach((location) => {
                        location.operatorList.forEach((operator) => {
                            const networkType = operator.networkType; // Example: "3G", "4G", "5G"
                            const operatorName = operator.operatorName.toLowerCase(); // Normalize case

                            if (!networkGroups[networkType]) {
                                networkGroups[networkType] = new Set(); // Use a Set to avoid duplicates
                            }
                            networkGroups[networkType].add(operatorName);
                        });
                    });

                    // Select the container
                    const networkDetailsContainer = $("#networkGroups");
                    networkDetailsContainer.empty(); // Clear previous content

                    // Loop through each network type and create the HTML structure
                    Object.entries(networkGroups).forEach(([networkType, operators]) => {
                        const formattedOperators = Array.from(operators)
                            .map((name) => name.charAt(0).toUpperCase() + name.slice(1)) // Capitalize first letter
                            .join(", ");

                        // Choose correct icon based on network type
                        let iconClass = "e_mobiledata_badge"; // Default icon
                        if (networkType.includes("3G")) iconClass = "3g_mobiledata_badge";
                        else if (networkType.includes("4G")) iconClass = "4g_mobiledata_badge";
                        else if (networkType.includes("5G")) iconClass = "5g_mobiledata_badge";

                        // Append the network info to the container
                        networkDetailsContainer.append(`
                            <div class="singleAddInfoDet">
                                <span class="material-symbols-outlined">${iconClass}</span>
                                <p>${formattedOperators}</p>
                            </div>
                        `);
                    });

                    const formattedPrice = ((plan.price / 10000) * 2).toFixed(2);

                    // Format duration
                    const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;


                    $('#paymentForm [name="price"]').val((plan.price / 10000) * 2);
                    $('#paymentForm [name="currency"]').val('USD');
                    $('#paymentForm [name="package_code"]').val(packageCode);
                    $('#paymentForm [name="seller"]').val(seller);

                    $('#planDetailsModalLabel').html(plan.name);
                    $('.dataVolume').html(plan.formattedVolume);
                    $('.esimDuration').html(formattedDuration);
                    $('.esimPrice').html(`$${formattedPrice} USD`);
                    $('.countryImg img').attr('src', planImage);
                    $('.supportedCountriesAreaList').html(supportedCountriesList);
                    $('.planType').html(planType);
                    $('.supportTopUpType').html(plan.supportTopUpType === 2 ? "Available" : "Not Available");
                } else {
                    showToast('Error fecthing eSIM plan.', 'bg-danger');
                }
            },
            error: function () {
                showToast('Failed to fetch eSIM plan. Please try again later.', 'bg-danger');
            },
            complete: function () {
                loader.addClass("d-none");
            }
        });
    } else {
        $.ajax({
            url: "/api/esim/plan/esimgo/",
            type: "GET",
            data: { name: packageCode },
            success: function (response) {
                if (response.status) {
                    const plan = response.data;
                    console.log(plan);

                    // Determine Plan Name
                    if (type == 'single') {
                        planImage = `https://flagcdn.com/w320/${locationCode.toLowerCase()}.png`;
                    } else {
                        planImage = `/static/img/regions/${locationCode.toLowerCase()}.png`;
                    }
                    // -----------------------------
                    // Format data, validity, price
                    // -----------------------------
                    const volume = plan.formattedVolume || "Unlimited";
                    const formattedPrice = plan.formattedPrice || price || "0.00";
                    const duration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

                    // -----------------------------
                    // Build "Supported Countries" List
                    // -----------------------------
                    let supportedCountriesList = "";
                    if (plan.roamingEnabled === null) {
                        countries = plan.countries
                    } else {
                        countries = plan.roamingEnabled
                    }
                    countries.forEach((item) => {
                        const isoCode = item.country.iso.toLowerCase();
                        const countryName = item.country.name;
                        supportedCountriesList += `
                            <div class="oneSupportedCountry">
                                <img src="https://flagcdn.com/w320/${isoCode}.png" alt="">
                                <h1>${countryName}</h1>
                            </div>
                        `;
                    });

                    // -----------------------------
                    // Build "Network(s)" Info
                    // -----------------------------
                    const speedGroups = {};

                    // Iterate over countries and networks
                    countries.forEach((ctry) => {
                        // Guard against null/undefined or non-array
                        if (!Array.isArray(ctry.networks)) {
                            return; // Skip this country if `networks` is missing or invalid
                        }

                        ctry.networks.forEach((net) => {
                            // Sometimes `net` could be null or missing, so check:
                            if (!net || !Array.isArray(net.speeds)) {
                                return; // Skip this network if `net` or `net.speeds` is missing
                            }

                            net.speeds.forEach((speed) => {
                                // Initialize a set for this speed if it doesn't exist yet
                                if (!speedGroups[speed]) {
                                    speedGroups[speed] = new Set();
                                }

                                // net.name could also be null or undefined, so use a fallback if needed:
                                const operatorName = net.name || "Unknown";
                                speedGroups[speed].add(operatorName);
                            });
                        });
                    });

                    // Select the container for networks
                    const networkDetailsContainer = $("#networkGroups");
                    networkDetailsContainer.empty(); // Clear previous content

                    // Loop through each network type and create the formatted HTML structure
                    Object.entries(speedGroups).forEach(([speed, operatorsSet]) => {
                        const formattedOperators = Array.from(operatorsSet)
                            .map((name) => name.charAt(0).toUpperCase() + name.slice(1)) // Capitalize first letter
                            .join(", ");

                        // Choose the correct icon for the network type
                        let iconClass = "e_mobiledata_badge"; // Default icon
                        if (speed.includes("3G")) iconClass = "3g_mobiledata_badge";
                        else if (speed.includes("4G")) iconClass = "4g_mobiledata_badge";
                        else if (speed.includes("5G")) iconClass = "5g_mobiledata_badge";

                        // Append the network info to the container
                        networkDetailsContainer.append(`
                            <div class="singleAddInfoDet">
                                <span class="material-symbols-outlined">${iconClass}</span>
                                <p>${formattedOperators}</p>
                            </div>
                        `);
                    });


                    
                    $('#paymentForm [name="price"]').val(plan.price * 2);
                    $('#paymentForm [name="currency"]').val('USD');
                    $('#paymentForm [name="package_code"]').val(packageCode);
                    $('#paymentForm [name="seller"]').val(seller);

                    $('#planDetailsModalLabel').html(plan.description);
                    $('.dataVolume').html(volume);
                    $('.esimDuration').html(duration);
                    $('.esimPrice').html(`$${formattedPrice} USD`);
                    $('.countryImg img').attr('src', planImage);
                    $('.supportedCountriesAreaList').html(supportedCountriesList);
                    $('.planType').html('Data Only');
                    $('.supportTopUpType').html("Available");
                } else {
                    // If response.status is false
                    showToast("Error fetching unlimited eSIM plan.", "bg-danger");
                }
            },
            error: function () {
                showToast("Failed to fetch unlimited eSIM plan. Please try again later.", "bg-danger");
            },
            complete: function () {
                loader.addClass("d-none");
            }
        });
    }
});


// Handle form submission for eSIM plan purchase
$(document).on('submit', '#paymentForm', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

    var formData = JSON.stringify({
        user: $('#paymentForm [name="user"]').val(),
        price: $('#paymentForm [name="price"]').val(),
        currency: $('#paymentForm [name="currency"]').val(),
        package_code: $('#paymentForm [name="package_code"]').val(),
        seller: $('#paymentForm [name="seller"]').val(),
        payment_gateway: $('#paymentForm [name="payment_gateway"]:checked').val(),
    });

    $.ajax({
        url: '/api/payments/',
        method: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            showToast(response.message, 'bg-success');
            if (response.data.payment_gateway === 'CoinPayments') {
                window.open(response.data.payment_url, '_blank');
            }
            // window.location.href = '/orders';
        },
        error: function (error) {
            console.error(error);
            if (error.responseJSON.message && error.responseJSON.message !== undefined) {
                showToast(error.responseJSON.message, 'bg-danger');
            } else {
                showToast('Server error! Try again later.', 'bg-danger');
            }
        },
        complete: function () {
            loader.addClass("d-none");
        }
    });
});