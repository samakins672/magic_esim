
$(document).ready(function () {
	// Handle click on a country to fetch eSIM plans
	$(document).on('click', '.show-country-esims', function (e) {
		const locationCode = $(this).data("location_code");

		// Show loading spinner (block UI)
		$("#navs-pills-justified-local").block({
			message: '<div class="spinner-border text-white" role="status"></div>',
			css: {
				backgroundColor: "transparent",
				border: "0"
			},
			overlayCSS: {
				opacity: .5
			}
		});

		// Fetch eSIM plans via AJAX
		$.ajax({
			url: '/api/esim/plans/', // API endpoint
			type: 'GET',
			data: { locationCode: locationCode }, // Send location code as query parameter
			success: function (response) {
				if (response.status) {
					if (!response.data || !response.data.standard || response.data.standard.length === 0 || !response.data.standard.some(plan => plan.slug.startsWith(`${locationCode}_`))) {
						showToast('No eSIM plans available for this location.', 'bg-danger');
						return;
					}
					// Populate eSIM cards
					const planCards = $('#esim-plan-cards');
					const unlimitedCards = $('#unlimited-esim-plan-cards');
					planCards.empty(); // Clear previous content
					unlimitedCards.empty(); // Clear previous content
					// Filter and sort plans
					const sortedPlans = response.data.standard
						.filter(plan => plan.slug.startsWith(`${locationCode}_`) && !plan.slug.includes('_End') && !plan.slug.includes('_Daily')) // Filter by slug prefix and exclude slugs with "_End"
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)
					// Filter and sort plans
					const sortedUnlimited = response.data.unlimited
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)

					console.log(sortedPlans);
					console.log(sortedUnlimited);
					sortedPlans.forEach(plan => {
						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const card = `
						<div class="col-md-6">
							<div class="card shadow border-dark rounded-5 border-1 cursor-pointer show_plan_details" data-package_code="${plan.packageCode}"  data-plan_type="single" 
								data-price="${plan.formattedPrice}" data-currency="${plan.currencyCode}" data-location_code="${locationCode}" data-seller="esimaccess"
								data-bs-toggle="modal" data-bs-target="#planDetailsModal">
								<div class="card-header d-flex align-items-center justify-content-between p-4">
									<span class="d-flex flex-column align-items-start justify-content-between">
										<h5 class="m-0 fs-4 fw-bold text-dark">${plan.formattedVolume}</h5>
										<p class="m-0">${formattedDuration}</p>
									</span>
									<span class="fs-4 text-dark d-flex gap-2 align-items-center justify-content-between">
										$${plan.formattedPrice}
										<i class="bx bx-sm bxs-right-arrow-circle"></i>
									</span>
								</div>
							</div>
						</div>
						`;
						planCards.append(card);
					});

					sortedUnlimited.forEach(plan => {
						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const card = `
						<div class="col-md-6">
							<div class="card shadow border-dark rounded-5 border-1 cursor-pointer show_unlimited_details" data-package_code="${plan.name}"  data-plan_type="single" 
								data-price="${plan.formattedPrice}" data-currency="USD" data-location_code="${locationCode}" data-seller="esimgo"
								data-bs-toggle="modal" data-bs-target="#planDetailsModal">
								<div class="card-header d-flex align-items-center justify-content-between p-4">
									<span class="d-flex flex-column align-items-start justify-content-between">
										<h5 class="m-0 fs-4 fw-bold text-dark">${formattedDuration}</h5>
										<p class="m-0">∞ GB</p>
									</span>
									<span class="fs-4 text-dark d-flex gap-2 align-items-center justify-content-between">
										$${plan.formattedPrice}
										<i class="bx bx-sm bxs-right-arrow-circle"></i>
									</span>
								</div>
							</div>
						</div>
						`;
						unlimitedCards.append(card);
					});

					// Show eSIM plans, hide countries
					$('.esim_country').text(sortedPlans[0].locationNetworkList[0].locationName);
					$('.local_esim_flag').attr('src', `https://flagcdn.com/w320/${locationCode.toLowerCase()}.png`);
					$('.esim_local_hero').attr('style', `background: linear-gradient(rgb(0 0 0 / 0%), rgb(0 0 0 / 80%)), url('${response.data.unlimited[0].imageUrl}') center center; height: 30vh; background-size: cover;`);
					$('#countries-list').addClass('d-none');
					$('.esims_show').removeClass('d-none');
				} else {
					showToast('No eSIM plans available for this location.', 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plans. Please try again later.', 'bg-danger');
			},
			complete: function () {
				// Unblock UI
				$("#navs-pills-justified-local").unblock();
			}
		});
	});

	// Handle click on a region to fetch eSIM plans
	$(document).on('click', '.show-region-esims', function (e) {
		const locationCode = $(this).data("location_code");

		// Show loading spinner (block UI)
		$("#navs-pills-justified-regions").block({
			message: '<div class="spinner-border text-white" role="status"></div>',
			css: {
				backgroundColor: "transparent",
				border: "0"
			},
			overlayCSS: {
				opacity: .5
			}
		});

		// Fetch eSIM plans via AJAX
		$.ajax({
			url: '/api/esim/plans/',
			type: 'GET',
			data: { locationCode: '!RG' },
			success: function (response) {
				if (response.status) {
					// Populate eSIM cards
					const planCards = $('#esim-region-cards');
					planCards.empty(); // Clear previous content
					// Filter and sort plans
					const sortedPlans = response.data.standard
						.filter(plan => plan.slug.startsWith(`${locationCode}-`)) // Filter by slug prefix
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)

					sortedPlans.forEach(plan => {
						// Format price (last 4 digits as decimal)
						const formattedPrice = ((plan.price / 10000) * 2).toFixed(2);

						// Format data volume (MB if less than 1GB)
						const formattedVolume = plan.volume < 1024 ** 3
							? `${(plan.volume / (1024 ** 2)).toFixed(0)} MB` // Convert to MB
							: `${(plan.volume / (1024 ** 3)).toFixed(1)} GB`; // Convert to GB

						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const locationCount = plan.locationNetworkList.length;
						const locationText = locationCount > 1 ? `${locationCount} Countries` : `${locationCount} Country`;

						const card = `
                <div class="col-md-4 mb-4">
                  <div class="card shadow border-primary rounded-5 border-1">
                    <div class="card-header d-flex align-items-center justify-content-between text-dark fw-bolder">
                      <h5 class="m-0">${plan.name}</h5>
                      <img src="/static/img/regions/${locationCode.toLowerCase()}.png" class="rounded" style="width: 40px; height: auto;">
                    </div>
                    <div class="card-body text-center">
                      <ul class="list-unstyled text-start mb-4">
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Coverage:</strong> <span class="badge bg-label-primary p-2 fs-6">${locationText}</ class="btn btn-outline-primary"></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Data:</strong> <span>${formattedVolume}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Validity:</strong> <span>${formattedDuration}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top border-bottom"><strong>Price:</strong> <span class="fs-5 text-primary">$${formattedPrice} ${plan.currencyCode}</span></li>
                      </ul>
                      <button class="btn btn-outline-primary rounded-pill w-100 show_plan_details py-3" data-package_code="${plan.packageCode}"  data-plan_type="region" 
					  	data-price="${formattedPrice}" data-currency="${plan.currencyCode}" data-location_code="${locationCode}" data-seller="esimaccess"
						data-bs-toggle="modal" data-bs-target="#planDetailsModal">Buy Now</button>
                    </div>
                  </div>
                </div>
              `;
						planCards.append(card);
					});
					back_button = `
              <div class="text-center">
                <button id="back-to-regions-btn" class="btn btn-md rounded-pill btn-primary mt-4">Back to Regions</button>
              </div>
            `;
					planCards.append(back_button);

					// Show eSIM plans, hide countries
					$('#regions-list').addClass('d-none');
					$('#esim-region-cards').removeClass('d-none');
				} else {
					showToast('No eSIM plans available for this location.', 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plans. Please try again later.', 'bg-danger');
			},
			complete: function () {
				// Unblock UI
				$("#navs-pills-justified-regions").unblock();
			}
		});
	});

	// Handle click on a global to fetch eSIM plans
	$(document).on('click', '.show-global-esims', function (e) {
		const locationCode = $(this).data("location_code");

		// Show loading spinner (block UI)
		$("#navs-pills-justified-global").block({
			message: '<div class="spinner-border text-white" role="status"></div>',
			css: {
				backgroundColor: "transparent",
				border: "0"
			},
			overlayCSS: {
				opacity: .5
			}
		});

		// Fetch eSIM plans via AJAX
		$.ajax({
			url: '/api/esim/plans/',
			type: 'GET',
			data: { locationCode: '!GL' },
			success: function (response) {
				if (response.status) {
					// Populate eSIM cards
					const planCards = $('#esim-global-cards');
					planCards.empty(); // Clear previous content
					// Filter and sort plans
					const sortedPlans = response.data.standard
						.filter(plan => plan.slug.startsWith(`${locationCode}`)) // Filter by slug prefix
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)

					sortedPlans.forEach(plan => {
						// Format price (last 4 digits as decimal)
						const formattedPrice = ((plan.price / 10000) * 2).toFixed(2);

						// Format data volume (MB if less than 1GB)
						const formattedVolume = plan.volume < 1024 ** 3
							? `${(plan.volume / (1024 ** 2)).toFixed(0)} MB` // Convert to MB
							: `${(plan.volume / (1024 ** 3)).toFixed(1)} GB`; // Convert to GB

						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const locationCount = plan.locationNetworkList.length;
						const locationText = locationCount > 1 ? `${locationCount} Countries` : `${locationCount} Country`;

						const card = `
                <div class="col-md-4 mb-4">
                  <div class="card shadow border-primary border-1 rounded-5">
                    <div class="card-header d-flex align-items-center justify-content-between text-dark fw-bolder">
                      <h5 class="m-0">${plan.name}</h5>
                      <img src="/static/img/regions/as.png" class="rounded" style="width: 40px; height: auto;">
                    </div>
                    <div class="card-body text-center">
                      <ul class="list-unstyled text-start mb-4">
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Coverage:</strong> <span class="badge bg-label-primary p-2 fs-6">${locationText}</ class="btn btn-outline-primary"></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Data:</strong> <span>${formattedVolume}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Validity:</strong> <span>${formattedDuration}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top border-bottom"><strong>Price:</strong> <span class="fs-5 text-primary">$${formattedPrice} ${plan.currencyCode}</span></li>
                      </ul>
                      <button class="btn btn-outline-primary rounded-pill w-100 show_plan_details py-3" data-package_code="${plan.packageCode}"  data-plan_type="global" 
					  	data-price="${formattedPrice}" data-currency="${plan.currencyCode}" data-location_code="${locationCode}" data-seller="esimaccess"
						data-bs-toggle="modal" data-bs-target="#planDetailsModal">Buy Now</button>
                    </div>
                  </div>
                </div>
              `;
						planCards.append(card);
					});
					back_button = `
              <div class="text-center">
                <button id="back-to-global-btn" class="btn btn-md rounded-pill btn-primary mt-4">Back to Global</button>
              </div>
            `;
					planCards.append(back_button);

					// Show eSIM plans, hide countries
					$('#global-list').addClass('d-none');
					$('#esim-global-cards').removeClass('d-none');
				} else {
					showToast('No eSIM plans available for this location.', 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plans. Please try again later.', 'bg-danger');
			},
			complete: function () {
				// Unblock UI
				$("#navs-pills-justified-global").unblock();
			}
		});
	});

	// Handle "Back to Countries" button
	$(document).on('click', '#back-to-countries-btn', function (e) {
		$('.esims_show').addClass('d-none');
		$('#countries-list').removeClass('d-none');

		// Smooth scroll to the landing_esim
		const landing_esim = document.getElementById('landingESIM');
		landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
	});

	// Handle "Back to Regions" button
	$(document).on('click', '#back-to-regions-btn', function (e) {
		$('#esim-region-cards').addClass('d-none');
		$('#regions-list').removeClass('d-none');

		// Smooth scroll to the landing_esim
		const landing_esim = document.getElementById('landingESIM');
		landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
	});

	// Handle "Back to Global" button
	$(document).on('click', '#back-to-global-btn', function (e) {
		$('#esim-global-cards').addClass('d-none');
		$('#global-list').removeClass('d-none');

		// Smooth scroll to the landing_esim
		const landing_esim = document.getElementById('landingESIM');
		landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
	});

	// Toggle countries
	$("#toggle-countries-btn").on("click", function () {
		const isShowingPopular = $(this).text() === "Show 200+ Countries";

		if (isShowingPopular) {
			// Show 200+ Countries
			$("#countries-list .country-item").removeClass("d-none");
			$(this).text("Show Popular Countries");
		} else {
			// Show only popular countries
			$("#countries-list .country-item").each(function () {
				if ($(this).data("popular") === "False" || $(this).data("popular") === false) {
					$(this).addClass("d-none");
				} else {
					$(this).removeClass("d-none");
				}
			});
			$(this).text("Show 200+ Countries");

			// Smooth scroll to the landing_esim
			const landing_esim = document.getElementById('landingESIM');
			landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	});

	// Handle click on "Show Plan Details" button
	$(document).on('click', '.show_plan_details', function (e) {
		const packageCode = $(this).data("package_code");
		const locationCode = $(this).data("location_code");
		const plan_type = $(this).data("plan_type");
		const price = $(this).data("price");
		const currency = $(this).data("currency");
		const seller = $(this).data("seller");

		$('#planDetailsForm [name="price"]').val(price);
		$('#planDetailsForm [name="currency"]').val(currency);
		$('#planDetailsForm [name="package_code"]').val(packageCode);
		$('#planDetailsForm [name="seller"]').val(seller);

		// Show loading spinner (block UI)
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
				// Unblock UI
				$("#planDetailsForm").unblock();
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
					plan.countries.forEach((item) => {
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
					plan.countries.forEach((ctry) => {
					ctry.networks.forEach((net) => {
						// net.speeds might be ["2G", "3G", "4G", "5G"]
						// net.name might be "MTN", "Airtel", ...
						if (Array.isArray(net.speeds)) {
						net.speeds.forEach((speed) => {
							if (!speedGroups[speed]) {
							speedGroups[speed] = new Set();
							}
							speedGroups[speed].add(net.name);
						});
						}
					});
					});

					// Now turn speedGroups into a readable string
					// e.g. "4G: Airtel, MTN\n5G: MTN"
					let networkDetails = "";
					Object.entries(speedGroups).forEach(([speed, operatorsSet]) => {
					// Convert set to array, join with commas
					const operatorList = Array.from(operatorsSet).join(", ");
					networkDetails += `${speed}: ${operatorList}<br>`; // or \n for new lines
					});

					// If you want to list speeds or other info, you can do so similarly

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

	// Handle form submission for eSIM plan purchase
	$(document).on('submit', '#planDetailsForm', function (e) {
		e.preventDefault();

		var submitButton = $('#submitBtn');
		submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

		var formData = JSON.stringify({
			user: $('#planDetailsForm [name="user"]').val(),
			price: $('#planDetailsForm [name="price"]').val(),
			currency: $('#planDetailsForm [name="currency"]').val(),
			package_code: $('#planDetailsForm [name="package_code"]').val(),
			seller: $('#planDetailsForm [name="seller"]').val(),
			payment_gateway: $('#planDetailsForm [name="payment_gateway"]').val(),
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
				window.location.href = '/orders';
			},
			error: function (error) {
				console.error(error);
				if (error.responseJSON.message.error && error.responseJSON.message.error !== undefined) {
					showToast(error.responseJSON.message.error, 'bg-danger');
				} else {
					showToast('Server error! Try again later.', 'bg-danger');
				}
			},
			complete: function () {
				// Revert button text and re-enable the button
				submitButton.html('Submit changes').attr('disabled', false);
			}
		});
	});

	// Listen for input changes in the search box
	$("#search_country").on("keyup", function () {
		let searchValue = $(this).val().toLowerCase(); // Get input and convert to lowercase

		$(".country-item").each(function () {
			let countryName = $(this).find("span").text().trim().toLowerCase(); // Get the country name

			// Show or hide based on match
			if (countryName.includes(searchValue)) {
				$(this).removeClass("d-none");
			} else {
				$(this).addClass("d-none");
			}
		});
	});
});
