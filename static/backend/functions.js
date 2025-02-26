
$(document).ready(function () {
	// Handle click on a country to fetch eSIM plans
	$(document).on('click', '.show-country-esims', function (e) {
		const locationCode = $(this).data("location_code");

		loader = $('.loading');
		loader.removeClass("d-none");

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
							<a href="esim/s/single/${locationCode}/${plan.packageCode}" class="oneBundle">
								<div class="bundleDetsA">
									<h1>${plan.formattedVolume}</h1>
									<h2>${formattedDuration}</h2>
								</div>
								<div class="bundleDetsB">
									<h1>$<span>${plan.formattedPrice}</span></h1>
									<span class="material-symbols-outlined">keyboard_arrow_right</span>
								</div>
							</a>
						`;
						planCards.append(card);
					});

					sortedUnlimited.forEach(plan => {
						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const card = `
							<a href="esim/u/single/${locationCode}/${plan.name}" class="oneBundle">
								<div class="bundleDetsA">
									<h1>${formattedDuration}</h1>
									<h2>Unlimited GB</h2>
								</div>
								<div class="bundleDetsB">
									<h1>$<span>${plan.formattedPrice}</span></h1>
									<span class="material-symbols-outlined">keyboard_arrow_right</span>
								</div>
							</a>
						`;
						unlimitedCards.append(card);
					});

					// Show eSIM plans, hide countries
					$('.esim_country').text(sortedPlans[0].locationNetworkList[0].locationName);
					$('.local_esim_flag').attr('src', `https://flagcdn.com/w320/${locationCode.toLowerCase()}.png`);
					$('.esim_local_hero').attr('src', response.data.unlimited[0].imageUrl);
					$('.localEsimArea').addClass('d-none');
					$('.regioneSims').addClass('d-none');
					$('.globaleSims').addClass('d-none');
					$('.packagesArea').removeClass('d-none');
				} else {
					showToast('No eSIM plans available for this location.', 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plans. Please try again later.', 'bg-danger');
			},
			complete: function () {
				loader.addClass("d-none");

				// Smooth scroll to the landing_esim
				const landing_esim = document.getElementById('eSim');
				landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});

	// Handle click on a region to fetch eSIM plans
	$(document).on('click', '.show-region-esims', function (e) {
		const locationCode = $(this).data("location_code");
		const region = $(this).data("region");

		loader = $('.loading');
		loader.removeClass("d-none");

		// Fetch eSIM plans via AJAX
		$.ajax({
			url: '/api/esim/plans/',
			type: 'GET',
			data: { locationCode: '!RG', region: region, description: region },
			success: function (response) {
				if (response.status) {
					// Populate eSIM cards
					const planCards = $('#esim-plan-cards');
					const unlimitedCards = $('#unlimited-esim-plan-cards');
					planCards.empty(); // Clear previous content
					unlimitedCards.empty(); // Clear previous content
					// Filter and sort plans
					const sortedPlans = response.data.standard
						.filter(plan => plan.slug.startsWith(`${locationCode}-`) && !plan.slug.includes('_End') && !plan.slug.includes('_Daily')) // Filter by slug prefix and exclude slugs with "_End"
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
							<a href="esim/s/region/${locationCode}/${plan.packageCode}" class="oneBundle">
								<div class="bundleDetsA">
									<h1>${plan.formattedVolume}</h1>
									<h2>${formattedDuration}</h2>
								</div>
								<div class="bundleDetsB">
									<h1>$<span>${plan.formattedPrice}</span></h1>
									<span class="material-symbols-outlined">keyboard_arrow_right</span>
								</div>
							</a>
						`;
						planCards.append(card);
					});

					sortedUnlimited.forEach(plan => {
						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const card = `
							<a href="esim/u/region/${locationCode}/${plan.name}" class="oneBundle">
								<div class="bundleDetsA">
									<h1>${formattedDuration}</h1>
									<h2>Unlimited GB</h2>
								</div>
								<div class="bundleDetsB">
									<h1>$<span>${plan.formattedPrice}</span></h1>
									<span class="material-symbols-outlined">keyboard_arrow_right</span>
								</div>
							</a>
						`;
						unlimitedCards.append(card);
					});

					planImageURL = response.data.unlimited.length > 0 ? response.data.unlimited[0].imageUrl : 'https://esimgo-cms-images-prod.s3.eu-west-1.amazonaws.com/North_America_bbe3181858.jpg';
					// Show eSIM plans, hide countries
					$('.esim_country').text(region);
					$('.local_esim_flag').attr('src', `/static/img/regions/${locationCode.toLowerCase()}.png`);
					$('.esim_local_hero').attr('src', planImageURL);
					$('.localEsimArea').addClass('d-none');
					$('.regioneSims').addClass('d-none');
					$('.globaleSims').addClass('d-none');
					$('.packagesArea').removeClass('d-none');
				} else {
					showToast('No eSIM plans available for this location.', 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plans. Please try again later.', 'bg-danger');
			},
			complete: function () {
				loader.addClass("d-none");

				// Smooth scroll to the landing_esim
				const landing_esim = document.getElementById('eSim');
				landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });	
			}
		});
	});

	// Handle click on a global to fetch eSIM plans
	$(document).on('click', '.show-global-esims', function (e) {
		const locationCode = $(this).data("location_code");
		const region = "Global";

		loader = $('.loading');
		loader.removeClass("d-none");

		// Fetch eSIM plans via AJAX
		$.ajax({
			url: '/api/esim/plans/',
			type: 'GET',
			data: { locationCode: '!GL', region: region, description: region },
			success: function (response) {
				if (response.status) {
					// Populate eSIM cards
					const planCards = $('#esim-plan-cards');
					const unlimitedCards = $('#unlimited-esim-plan-cards');
					planCards.empty(); // Clear previous content
					unlimitedCards.empty(); // Clear previous content
					// Filter and sort plans
					const sortedPlans = response.data.standard
						.filter(plan => plan.slug.startsWith(`${locationCode}`) && !plan.slug.includes('_End') && !plan.slug.includes('_Daily')) // Filter by slug prefix and exclude slugs with "_End"
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
							<a href="esim/s/region/${locationCode}/${plan.packageCode}" class="oneBundle">
								<div class="bundleDetsA">
									<h1>${plan.formattedVolume}</h1>
									<h2>${formattedDuration}</h2>
								</div>
								<div class="bundleDetsB">
									<h1>$<span>${plan.formattedPrice}</span></h1>
									<span class="material-symbols-outlined">keyboard_arrow_right</span>
								</div>
							</a>
						`;
						planCards.append(card);
					});

					sortedUnlimited.forEach(plan => {
						// Format duration
						const formattedDuration = plan.duration > 1 ? `${plan.duration} Days` : `${plan.duration} Day`;

						const card = `
							<a href="esim/u/region/${locationCode}/${plan.name}" class="oneBundle">
								<div class="bundleDetsA">
									<h1>${formattedDuration}</h1>
									<h2>Unlimited GB</h2>
								</div>
								<div class="bundleDetsB">
									<h1>$<span>${plan.formattedPrice}</span></h1>
									<span class="material-symbols-outlined">keyboard_arrow_right</span>
								</div>
							</a>
						`;
						unlimitedCards.append(card);
					});

					// Show eSIM plans, hide countries
					$('.esim_country').text(region);
					$('.local_esim_flag').attr('src', `/static/img/regions/${locationCode.toLowerCase()}.png`);
					$('.esim_local_hero').attr('src', '/static/img/illustrations/world-map.png');
					$('.localEsimArea').addClass('d-none');
					$('.regioneSims').addClass('d-none');
					$('.globaleSims').addClass('d-none');
					$('.packagesArea').removeClass('d-none');
				} else {
					showToast('No eSIM plans available for this location.', 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plans. Please try again later.', 'bg-danger');
			},
			complete: function () {
				loader.addClass("d-none");

				// Smooth scroll to the landing_esim
				const landing_esim = document.getElementById('eSim');
				landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});

	// Handle "Back to Countries" button
	$(document).on('click', '#back-to-countries-btn', function (e) {
		$('.localEsimArea').removeClass('d-none');
		$('.packagesArea').addClass('d-none');

		// Remove aria-selected from all buttons
		$('.eSimAcBtns button').attr('aria-selected', 'false');

		// Smooth scroll to the landing_esim
		const landing_esim = document.getElementById('eSim');
		landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
	});

	// Toggle countries
	$("#toggle-countries-btn").on("click", function () {
		const isShowingPopular = $(this).text() === "Show All Countries";

		if (isShowingPopular) {
			// Show All Countries
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
			$(this).text("Show All Countries");

		}
		
		// Smooth scroll to the landing_esim
		const landing_esim = document.getElementById('eSim');
		landing_esim.scrollIntoView({ behavior: 'smooth', block: 'start' });
	});

	// Listen for input changes in the search box
	$("#search_country").on("keyup", function () {
		let searchValue = $(this).val().toLowerCase(); // Get input and convert to lowercase

		$(".country-item").each(function () {
			let countryName = $(this).find("h1").text().trim().toLowerCase(); // Get the country name

			// Show or hide based on match
			if (countryName.includes(searchValue)) {
				$(this).removeClass("d-none");
			} else {
				$(this).addClass("d-none");
			}
		});
	});

	$('.eSimAcBtns button').on('click', function () {
		// Get target content area from data-target
		const target = $(this).data('target');

		// Remove aria-selected from all buttons
		$('.eSimAcBtns button').attr('aria-selected', 'false');

		// Add aria-selected to the clicked button
		$(this).attr('aria-selected', 'true');

		// Hide all content areas
		$('.localEsimArea, .regioneSims, .globaleSims, .packagesArea').addClass('d-none');

		// Show the corresponding content area
		$(target).removeClass('d-none');
	});
});
