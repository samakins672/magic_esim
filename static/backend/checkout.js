$(document).ready(function () {
    const packageCode = $("#package_code").val();
    const locationCode = $("#location_code").val();
    const type = $("#type").val();
    const plan_type = $("#plan_type").val();

    const price = $(this).data("price");
    const currency = $(this).data("currency");
    const seller = $(this).data("seller");

    $('#planDetailsForm [name="price"]').val(price);
    $('#planDetailsForm [name="currency"]').val(currency);
    $('#planDetailsForm [name="package_code"]').val(packageCode);
    $('#planDetailsForm [name="seller"]').val(seller);

    loader = $('.loading');
    loader.removeClass("d-none");

    // Fetch eSIM plans via AJAX
    $.ajax({
        url: '/api/esim/plans/', // API endpoint
        type: 'GET',
        data: { packageCode: packageCode }, // Send location code as query parameter
        success: function (response) {
            if (response.status) {
                // Populate eSIM cards
                const planCards = $('#esim_plan_details');
                const planCardsOther = $('#esim_plan_other_details');
                planCards.empty();
                planCardsOther.empty();


                // Filter and sort plans
                const sortedPlans = response.data.standard
                    .sort((a, b) => a.price - b.price); // Sort by price (ascending)

                const plan = sortedPlans[0];
                const locationDetails = plan.locationNetworkList;

                // Determine Plan Name
                if (plan_type == 'single') {
                    planImage = `https://flagcdn.com/w320/${plan.locationNetworkList[0].locationCode.toLowerCase()}.png`;
                    planName = plan.locationNetworkList[0].locationName;
                } else {
                    const locationCount = plan.locationNetworkList.length;
                    if (plan_type == 'region') {
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
						<li class="py-2 border-bottom d-flex align-items-center justify-content-between">
						<p class="mb-0">${location.locationName}</p>
						<img src="https://flagcdn.com/w320/${location.locationCode.toLowerCase()}.png" class="img-fluid rounded" style="height:35px; width:60px;">
						</li>
					`
                    )
                    .join("");

                // Process the `locationNetworkList` to merge networks globally and group by network type
                const networkGroups = {};

                // Iterate through all locations and their operators
                locationDetails.forEach((location) => {
                    location.operatorList.forEach((operator) => {
                        const networkType = operator.networkType;
                        const operatorName = operator.operatorName.toLowerCase(); // Normalize case

                        if (!networkGroups[networkType]) {
                            networkGroups[networkType] = new Set(); // Use a Set to avoid duplicates
                        }
                        networkGroups[networkType].add(operatorName);
                    });
                });

                // Convert the networkGroups map to a formatted string
                const networkDetails = Object.entries(networkGroups)
                    .map(
                        ([networkType, operators]) =>
                            `${networkType}: ${Array.from(operators)
                                .map((name) => name.charAt(0).toUpperCase() + name.slice(1)) // Capitalize operator names
                                .join(", ")}`
                    )
                    .join("<hr class='my-2'>");


                const formattedPrice = ((plan.price / 10000) * 2).toFixed(2);

                // Format data volume (MB if less than 1GB)
                const formattedVolume = plan.volume < 1024 ** 3
                    ? `${(plan.volume / (1024 ** 2)).toFixed(0)} MB` // Convert to MB
                    : `${(plan.volume / (1024 ** 3)).toFixed(1)} GB`; // Convert to GB

                // Format duration
                const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

                const details = `
						<div class="card shadow flex-md-row align-items-center border-primary border-1">
                          <div class="col-12 col-md-6 text-center pt-md-0 pt-5">
                            <img src="${planImage}" class="img-fluid rounded-4">
                          </div>
                          <div class="card-body col-12 col-md-6">
                            <ul class="list-unstyled text-start mb-4">
                              <li class="d-flex flex-row justify-content-between fw-bold py-4">
                                <strong>Coverage:</strong> <span>${planName}</span></li>
                              <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top">
                                <strong>Data:</strong> <span>${formattedVolume}</span></li>
                              <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top">
                                <strong>Validity:</strong> <span>${formattedDuration}</span></li>
                              <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top">
                                <strong>Price:</strong> <span class="fs-5 text-primary">$${formattedPrice} ${plan.currencyCode}</span></li>
                            </ul>
                          </div>
                        </div>
					`;

                const otherDetails = `
						<div class="col-12 col-md-6 p-5">
                          <h5 class="m-0 text-primary fw-bold">Supported Countries</h5>
                          <div class="text-center overflow-auto" style="max-height: 350px">
                            <ul class="list-unstyled text-start mb-0" id="vertical-scroll_bar">
								${supportedCountriesList}
                            </ul>
                          </div>
                        </div>
                        <div class="col-12 col-md-6 card bg-lighter">
                          <div class="card-header pb-2 text-dark fw-bolder">
                            <h5 class="m-0 text-primary fw-bold">Additional Information</h5>
                          </div>
                          <div class="card-body text-center">
                            <ul class="list-unstyled text-start mb-0">
                              <li class="py-2 d-flex align-items-center text-dark">
                                <i class="bx bx-broadcast me-3"></i>
                                <div class="overflow-auto" style="max-height: 100px">
                                  <p class="mb-1">Network(s):</p>
                                  <span class="fw-bold">${networkDetails}</span>
                                </div>
                              </li>
                              <li class="py-2 d-flex align-items-center text-dark">
                                <i class="bx bx-message-alt-detail me-3"></i>
                                <div>
                                  <p class="mb-0">Plan Type:
                                  </p>
                                  <span class="fw-bold">${planType}</span>
                                </div>
                              </li>
                              <li class="py-2 d-flex align-items-center text-dark">
                                <i class="bx bx-list-check me-3"></i>
                                <div>
                                  <p class="mb-0">Validity Policy:</p>
                                  <span class="fw-bold">The validity period starts when the eSIM connects to a mobile
                                    network in its coverage area. If you install the eSIM outside of the coverage area,
                                    you can connect to a network when you arrive.</span>
                                </div>
                              </li>
                              <li class="py-2 d-flex align-items-center text-dark">
                                <i class="bx bxs-layer-plus me-3"></i>
                                <div>
                                  <p class="mb-0">Top-Up Option</p>
                                  <span class="fw-bold">${plan.supportTopUpType === 2 ? "Available" : "Not Available"
                    }</span>
                                </div>
                              </li>
                            </ul>
                          </div>
                        </div>
					`;
                $('#planDetailsModalLabel').html(plan.name);
                planCards.html(details);
                planCardsOther.html(otherDetails);
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
});

// Fetch and Display eSIM-Go "Unlimited" Plan Details
$(document).on('click', '.show_unlimited_details', function (e) {
    // 1) Gather data from button's data- attributes
    const planName = $(this).data("package_code");
    const price = $(this).data("price");
    const currency = $(this).data("currency");

    // If you're reusing the same modal form fields:
    $('#planDetailsForm [name="price"]').val(price);
    $('#planDetailsForm [name="currency"]').val(currency);
    $('#planDetailsForm [name="package_code"]').val(planName);
    $('#planDetailsForm [name="seller"]').val('esimgo');

    // 2) Show loading spinner
    $("#planDetailsForm").block({
        message: `<br><br>Loading details...<br>`,
        css: {
            backgroundColor: "transparent",
            border: "0"
        },
        overlayCSS: {
            opacity: .5
        }
    });

    // 3) Make AJAX call to your new unlimited bundle endpoint
    $.ajax({
        url: "/api/esim/plan/esimgo/",   // Endpoint for unlimited details
        type: "GET",
        data: { name: planName },       // 'name' param e.g. 'esim_ULE_1D_CN_V2'
        success: function (response) {
            if (response.status) {
                // 4) Parse the single plan object
                const plan = response.data;  // plan has fields like .name, .description, .countries[], .formattedPrice, etc.

                // Clear the display areas
                const planCards = $('#esim_plan_details');
                const planCardsOther = $('#esim_plan_other_details');
                planCards.empty();
                planCardsOther.empty();

                // -----------------------------
                // Build coverage image & name
                // -----------------------------
                // eSIM-Go might have multiple countries in 'plan.countries', we can display them all:
                const countryCount = plan.countries.length;
                let planImage = plan.imageUrl || "";            // use plan.imageUrl if available
                let planNameUI = countryCount === 1
                    ? plan.countries[0].country.name               // e.g. "China"
                    : `${countryCount} Countries`;                 // e.g. "3 Countries"

                // If you want to use the first country's ISO for a flag image:
                // planImage = `https://flagcdn.com/w320/${plan.countries[0].country.iso.toLowerCase()}.png`;

                // -----------------------------
                // Format data, validity, price
                // -----------------------------
                const volume = plan.formattedVolume || "Unlimited";
                const formattedPrice = plan.formattedPrice || price || "0.00";
                const duration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

                // -----------------------------
                // Generate HTML for #esim_plan_details
                // -----------------------------
                const details = `
						<div class="card shadow flex-md-row align-items-center border-primary rounded-3 border-1">
						<div class="col-12 col-md-6 text-center pt-md-0 pt-5">
							<img src="${planImage}" class="img-fluid rounded-4">
						</div>
						<div class="card-body col-12 col-md-6">
							<ul class="list-unstyled text-start mb-4">
							<li class="d-flex flex-row justify-content-between fw-bold py-4">
								<strong>Coverage:</strong> <span>${planNameUI}</span>
							</li>
							<li class="d-flex flex-row justify-content-between fw-bold py-4 border-top">
								<strong>Data:</strong> <span>${volume}</span>
							</li>
							<li class="d-flex flex-row justify-content-between fw-bold py-4 border-top">
								<strong>Validity:</strong> <span>${duration}</span>
							</li>
							<li class="d-flex flex-row justify-content-between fw-bold py-4 border-top">
								<strong>Price:</strong> 
								<span class="fs-5 text-primary">$${formattedPrice} ${currency}</span>
							</li>
							</ul>
						</div>
						</div>
					`;
                planCards.html(details);

                // -----------------------------
                // Build "Supported Countries" List
                // -----------------------------
                let supportedCountriesList = "";
                if (plan.roamingEnabled === null) {
                    countries = plan.countries
                } else {
                    countries = plan.roamingEnabled
                    console.log(countries)
                }
                countries.forEach((item) => {
                    const isoCode = item.country.iso.toLowerCase();
                    const countryName = item.country.name;
                    supportedCountriesList += `
							<li class="py-2 border-bottom d-flex align-items-center justify-content-between">
								<p class="mb-0">${countryName}</p>
								<img src="https://flagcdn.com/w320/${isoCode}.png" class="img-fluid rounded" style="height:35px; width:60px;">
							</li>
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

                // Now turn speedGroups into a readable string
                // e.g. "4G: Airtel, MTN\n5G: MTN"
                let networkDetails = "";
                Object.entries(speedGroups).forEach(([speed, operatorsSet]) => {
                    // Convert set to array, join with commas
                    const operatorList = Array.from(operatorsSet).join(", ");
                    networkDetails += `${speed}: ${operatorList}<hr>`;
                });


                // Build #esim_plan_other_details HTML
                // Example: Reuse the same layout from your "Additional Information" card
                const otherDetails = `
						<div class="col-12 col-md-6 p-5">
						<h5 class="m-0 text-primary fw-bold">Supported Countries</h5>
						<div class="text-center overflow-auto" style="max-height: 350px">
							<ul class="list-unstyled text-start mb-0" id="vertical-scroll_bar">
							${supportedCountriesList}
							</ul>
						</div>
						</div>
						<div class="col-12 col-md-6 card bg-lighter">
						<div class="card-header pb-2 text-dark fw-bolder">
							<h5 class="m-0 text-primary fw-bold">Additional Information</h5>
						</div>
						<div class="card-body text-center">
							<ul class="list-unstyled text-start mb-0">
							<li class="py-2 d-flex align-items-center text-dark">
								<i class="bx bx-broadcast me-3"></i>
								<div class="overflow-auto" style="max-height: 100px">
								<p class="mb-1">Network(s):</p>
								<span class="fw-bold">${networkDetails}</span>
								</div>
							</li>
							<li class="py-2 d-flex align-items-center text-dark">
								<i class="bx bx-list-check me-3"></i>
								<div>
								<p class="mb-0">Validity Policy:</p>
								<span class="fw-bold">
									The validity period starts when the eSIM connects to a mobile network in its coverage area.
									If you install the eSIM outside of the coverage area, you can connect when you arrive.
								</span>
								</div>
							</li>
							<li class="py-2 d-flex align-items-center text-dark">
								<i class="bx bxs-layer-plus me-3"></i>
								<div>
								<p class="mb-0">Auto-Start</p>
								<span class="fw-bold">${plan.autostart ? "Yes" : "No"}</span>
								</div>
							</li>
							</ul>
						</div>
						</div>
					`;
                $('#planDetailsModalLabel').html(plan.description);
                planCardsOther.html(otherDetails);

            } else {
                // If response.status is false
                showToast("Error fetching unlimited eSIM plan.", "bg-danger");
            }
        },
        error: function () {
            showToast("Failed to fetch unlimited eSIM plan. Please try again later.", "bg-danger");
        },
        complete: function () {
            // 5) Unblock UI
            $("#planDetailsForm").unblock();
        }
    });
});
