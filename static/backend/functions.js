
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
					// Populate eSIM cards
					const planCards = $('#esim-plan-cards');
					planCards.empty(); // Clear previous content
					// Filter and sort plans
					const sortedPlans = response.data.packageList
						.filter(plan => plan.slug.startsWith(`${locationCode}_`)) // Filter by slug prefix
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)

					sortedPlans.forEach(plan => {
						// Format price (last 4 digits as decimal)
						const formattedPrice = (plan.price / 10000).toFixed(2);

						// Format data volume (MB if less than 1GB)
						const formattedVolume = plan.volume < 1024 ** 3
							? `${(plan.volume / (1024 ** 2)).toFixed(0)} MB` // Convert to MB
							: `${(plan.volume / (1024 ** 3)).toFixed(1)} GB`; // Convert to GB

						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const card = `
                <div class="col-md-4 mb-4">
                  <div class="card shadow border-1">
                    <div class="card-header d-flex align-items-center justify-content-between text-dark fw-bolder">
                      <h5 class="m-0">${plan.name}</h5>
                      <img src="https://flagcdn.com/w320/${locationCode.toLowerCase()}.png" class="rounded" style="width: 80px; height: auto;">
                    </div>
                    <div class="card-body text-center">
                      <ul class="list-unstyled text-start mb-4">
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Coverage:</strong> <span>${plan.locationNetworkList[0].locationName}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Data:</strong> <span>${formattedVolume}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Validity:</strong> <span>${formattedDuration}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top border-bottom"><strong>Price:</strong> <span class="fs-5 text-primary">$${formattedPrice} ${plan.currencyCode}</span></li>
                      </ul>
                      <button class="btn btn-outline-primary w-100 buy-plan py-3" data-package-code="${plan.packageCode}">Buy Now</button>
                    </div>
                  </div>
                </div>
              `;
						planCards.append(card);
					});
					back_button = `
              <div class="text-center">
                <button id="back-to-countries-btn" class="btn btn-md rounded-pill btn-primary mt-4">Back to Countries</button>
              </div>
            `;
					planCards.append(back_button);

					// Show eSIM plans, hide countries
					$('#countries-list').addClass('d-none');
					$('#esim-plan-cards').removeClass('d-none');
				} else {
					alert('No eSIM plans available for this location.');
				}
			},
			error: function () {
				alert('Failed to fetch eSIM plans. Please try again later.');
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
					const sortedPlans = response.data.packageList
						.filter(plan => plan.slug.startsWith(`${locationCode}-`)) // Filter by slug prefix
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)

					sortedPlans.forEach(plan => {
						// Format price (last 4 digits as decimal)
						const formattedPrice = (plan.price / 10000).toFixed(2);

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
                  <div class="card shadow border-1">
                    <div class="card-header d-flex align-items-center justify-content-between text-dark fw-bolder">
                      <h5 class="m-0">${plan.name}</h5>
                      <img src="/static/img/regions/${locationCode.toLowerCase()}.png" class="rounded" style="width: 50px; height: auto;">
                    </div>
                    <div class="card-body text-center">
                      <ul class="list-unstyled text-start mb-4">
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Coverage:</strong> <span class="btn btn-label-primary">${locationText}</ class="btn btn-outline-primary"></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Data:</strong> <span>${formattedVolume}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Validity:</strong> <span>${formattedDuration}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top border-bottom"><strong>Price:</strong> <span class="fs-5 text-primary">$${formattedPrice} ${plan.currencyCode}</span></li>
                      </ul>
                      <button class="btn btn-outline-primary w-100 buy-plan py-3" data-package-code="${plan.packageCode}">Buy Now</button>
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
					alert('No eSIM plans available for this location.');
				}
			},
			error: function () {
				alert('Failed to fetch eSIM plans. Please try again later.');
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
					const sortedPlans = response.data.packageList
						.filter(plan => plan.slug.startsWith(`${locationCode}`)) // Filter by slug prefix
						.sort((a, b) => a.price - b.price); // Sort by price (ascending)

					sortedPlans.forEach(plan => {
						// Format price (last 4 digits as decimal)
						const formattedPrice = (plan.price / 10000).toFixed(2);

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
                  <div class="card shadow border-1">
                    <div class="card-header d-flex align-items-center justify-content-between text-dark fw-bolder">
                      <h5 class="m-0">${plan.name}</h5>
                      <img src="/static/img/regions/as.png" class="rounded" style="width: 50px; height: auto;">
                    </div>
                    <div class="card-body text-center">
                      <ul class="list-unstyled text-start mb-4">
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Coverage:</strong> <span class="btn btn-label-primary">${locationText}</ class="btn btn-outline-primary"></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Data:</strong> <span>${formattedVolume}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top"><strong>Validity:</strong> <span>${formattedDuration}</span></li>
                        <li class="d-flex flex-row justify-content-between fw-bold py-4 border-top border-bottom"><strong>Price:</strong> <span class="fs-5 text-primary">$${formattedPrice} ${plan.currencyCode}</span></li>
                      </ul>
                      <button class="btn btn-outline-primary w-100 buy-plan py-3" data-package-code="${plan.packageCode}">Buy Now</button>
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
					alert('No eSIM plans available for this location.');
				}
			},
			error: function () {
				alert('Failed to fetch eSIM plans. Please try again later.');
			},
			complete: function () {
				// Unblock UI
				$("#navs-pills-justified-global").unblock();
			}
		});
	});

	// Handle "Back to Countries" button
	$(document).on('click', '#back-to-countries-btn', function (e) {
		$('#esim-plan-cards').addClass('d-none');
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
});