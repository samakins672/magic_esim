// Function to populate the eSIMs table
function populateEsimsTable(esims) {
    const $esimListCard = $("#esim_lists");
    $esimListCard.empty(); // Clear any existing rows

    esims.forEach((esim, index) => {
        const volume_left = esim.volume - esim.volume_used;

        // Calculate percentage of volume left
        const volumePercentage = Math.floor((volume_left / esim.volume) * 100);

        // Determine gradient colors based on percentage
        const gradientStart = "#BB1600";
        const gradientEnd = "#ffaba0";
        const colorStop = `${volumePercentage}%`;

        const backgroundColor = `linear-gradient(to right, ${gradientStart} ${colorStop}, ${gradientEnd} ${colorStop})`;

        // Format data volume (MB if less than 1GB)
        const volumeLeft = volume_left < 1024 ** 3
            ? `${(volume_left / 1024 ** 2).toFixed(0)} MB` // Convert to MB
            : `${(volume_left / 1024 ** 3).toFixed(1)} GB`; // Convert to GB

        // Call the function with the plan's data
        if (esim.activated_on == null) {
            durationDisplay = esim.duration > 1 ? `${esim.duration} Days` : `${esim.duration} Day`;
        } else {
            const { isExpired, durationLeft } = calculateRemainingDuration(esim.activated_on, esim.duration);
            durationDisplay = isExpired ? "Plan Expired" : `Left for ${durationLeft}`;
        }

        // Output the results
        console.log(esim.activated_on);
        const location_code = esim.location_code != null ? esim.location_code.toLowerCase() : 'ch';

        const row = `
        <div class="col-lg-4 col-md-6 col-12">
            <div class="card mb-4 shadow rounded-5 border border-primary border-1">
                <div class="card-body p-4">
                    <div class="d-flex flex-column justify-content-between p-4 rounded-4 mb-4 text-white fw-bold plan_card"
                        style="overflow: hidden; height: 200px; background: ${backgroundColor}; cursor: pointer;"
                        data-bs-toggle="offcanvas" data-bs-target="#planDetailsOffcanvas" aria-controls="planDetailsOffcanvas"
                        data-order_no="${esim.order_no}">
                        <span class="d-flex align-items-center">
                            <img class="me-2 rounded" src="https://flagcdn.com/w320/${location_code}.png" height="30px" width="45px">
                            <span>
                                ${esim.name} <br>
                                <small class="fw-light">Order No: ${esim.order_no}</small>
                            </span>
                        </span>
                        <span>
                            <span class="fs-4 fw-bolder mb-1 me-2">${volumeLeft}</span>
                            <span>Left for ${durationDisplay}</span>
                        </span>
                    </div>
                    <a href="#" class="btn btn-primary w-100 rounded-5">Buy more data</a>
                </div>
            </div>
        </div>
      `;

        $esimListCard.append(row);
    });
}

// Populate the table on page load
$(document).ready(function () {
    const mainCard = $("#esim_lists");
    blockUI(mainCard); // Show block UI

    $.ajax({
        url: "/api/esim/user/plans/",
        type: "GET",
        success: function (response) {
            console.log(response);
            populateEsimsTable(response);
            unblockUI(mainCard); // Remove block UI once data is loaded
        },
        error: function () {
            unblockUI(mainCard); // Remove block UI on error
            showToast("Failed to load data.", "bg-danger");
        },
    });


    
	// Handle click on "Show Plan Details" button
	$(document).on('click', '.plan_card', function (e) {
		const orderNo = $(this).data("order_no");

        const planProfile = $('#navs-top-profile');
        const planDataPlan = $('#navs-top-data_plan');
        planProfile.empty();
        planDataPlan.empty();

        const mainCard = $(".offcanvas-body");
        blockUI(mainCard); // Show block UI


		// Fetch eSIM plans via AJAX
		$.ajax({
			url: '/api/esim/profile/', // API endpoint
			type: 'GET',
			data: { orderNo: orderNo }, // Send location code as query parameter
			success: function (response) {
				if (response.status) {
					const plan = response.data[0];
                    console.log(plan);

                    const packageDetails = plan['packageList'][0]

					const formattedPrice = ((plan.price / 10000) * 2).toFixed(2);

					// Format duration
					const formattedDuration = plan.totalDuration > 1 ? `${plan.totalDuration} Days` : `${plan.totalDuration} Day`;

					const details = `
                        <div class="row g-5">
                            <div class="col-6">
                                <span>Time Created:</span>
                                <span class="fw-bold text-primary">${formatDateTime(packageDetails.createTime)}</span>
                            </div>
                            <div class="col-6">
                                <span>Time Activated:</span>
                                <span class="fw-bold text-success">${formatDateTime(plan.activateTime)}</span>
                            </div>
                            <div class="col-6">
                                <span>Expriry Time:</span>
                                <span class="fw-bold text-warning">${formatDateTime(plan.expiredTime)}</span>
                            </div>
                            <div class="col-6">
                                <span>eSIM status:</span>
                                <span class="fw-bold badge ${getBadgeColor(plan.esimStatus)}">${plan.esimStatus}</span>
                            </div>
                            <hr>
                            <div class="col-12">
                                <span>Transaction Id:</span>
                                <span class="fw-bold text-primary">${plan.transactionId}</span>
                            </div>
                            <div class="col-12">
                                <span>Activation code:</span>
                                <span class="fw-bold text-primary">${plan.ac}</span>
                            </div>
                            <hr>
                            <div class="col-12">
                                <span>ICCID:</span>
                                <span class="fw-bold text-primary">${plan.iccid}</span>
                            </div>
                            <div class="col-12">
                                <span>IMSI:</span>
                                <span class="fw-bold text-primary">${plan.imsi}</span>
                            </div>
                            <div class="col-12 fw-bold text-primary">
                                <span>QR code:</span>
                                <img src="${plan.qrCodeUrl}" class="img-fluid" width="150px">
                            </div>
                        </div>
					`;

					const dataDetails = `
                        <div class="row g-5">
                            <div class="col-6">
                                <span>Duration:</span>
                                <span class="fw-bold text-primary">${formattedDuration}</span>
                            </div>
                            <div class="col-6">
                                <span>Total data:</span>
                                <span class="fw-bold text-primary">${formatVolume(plan.totalVolume)}</span>
                            </div>
                            <div class="col-6">
                                <span>Time left:</span>
                                <span class="fw-bold text-primary">${calculateTimeLeft(plan.expiredTime)}</span>
                            </div>
                            <div class="col-6">
                                <span>Data left:</span>
                                <span class="fw-bold text-primary">${formatVolume(plan.totalVolume - plan.orderUsage)}</span>
                            </div>
                            <hr>
                            <div class="col-6">
                                <span>Total amount:</span>
                                <span class="fw-bold text-primary">$${formattedPrice}</span>
                            </div>
                            <div class="col-6">
                                <span>Region type:</span>
                                <span class="fw-bold text-primary">${packageDetails.packageName}</span>
                            </div>
                            <div class="col-6">
                                <span>Region:</span>
                                <span class="fw-bold text-uppercase text-primary">${packageDetails.locationCode}</span>
                            </div>
                            <div class="col-6">
                                <span>Data type:</span>
                                <span class="fw-bold text-primary">${plan.dataType === 1 ? "Mobile Data Only" : "Data and SMS"}</span>
                            </div>
                            <div class="col-6">
                                <span>Top up type:</span>
                                <span class="fw-bold text-primary">${plan.supportTopUpType === 2 ? "Supported" : "Not Supported"}</span>
                            </div>
                            <div class="col-6">
                                <span>APN:</span>
                                <span class="fw-bold text-primary">${plan.apn}</span>
                            </div>
                        </div>

					`;

					$('#planDetailsOffcanvasLabel').html(plan.name);
					planProfile.html(details);
					planDataPlan.html(dataDetails);
				} else {
					showToast(response.message, 'bg-danger');
				}
			},
			error: function () {
				showToast('Failed to fetch eSIM plan. Please try again later.', 'bg-danger');
			},
			complete: function () {
                unblockUI(mainCard);
			}
		});
	});
});