// Example eSIM API response
const esimsData = [
    {
        plan: "United Arab Emirates 20GB 30Days",
        status: "In Use",
        dataLeft: { gb: 16, percentage: 82 },
        timeLeft: { days: 28, hours: 23 },
        activateBefore: "2025-06-30",
        iccid: "89852240400025687146",
    },
    {
        plan: "United States 10GB 14Days",
        status: "Pending Activation",
        dataLeft: { gb: 10, percentage: 100 },
        timeLeft: { days: 14, hours: 0 },
        activateBefore: "2025-05-01",
        iccid: "89852240400025687147",
    },
];

// Function to populate the eSIMs table
function populateEsimsTable(esims) {
    const $esimListCard = $("#esim_lists");
    $esimListCard.empty(); // Clear any existing rows

    esims.forEach((esim) => {
        const row = `
        <div class="col-lg-4 col-md-6 col-12">
            <div class="card mb-4 shadow rounded-5 border border-primary border-1 plan-card"
                style="cursor: pointer;" data-bs-toggle="offcanvas" data-bs-target="#planDetailsOffcanvas"
                aria-controls="planDetailsOffcanvas">
                <div class="card-body p-4">
                <div class="d-flex flex-column justify-content-between p-4 rounded-4 mb-4 text-dark fw-bold"
                    style="overflow: hidden; height: 200px; background: linear-gradient(to right, #BB1600 30%, #ffaba0 30%);">
                    <span class="d-flex align-items-center">
                    <img class="me-2 rounded" src="https://flagcdn.com/w320/gb.png" height="30px" width="45px">
                    <span>
                        United Kingdom <br>
                        <small class="fw-light">Order No: ${esim.order_no}</small>
                    </span>
                    </span>
                    <span>
                    <span class="fs-4 fw-bolder mb-1 me-2">750 MB</span>
                    <span>Left for 2 days</span>
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

// Helper function to format date (e.g., "2025-06-30" -> "Jun 30, 2025")
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const monthNames = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];
    const day = date.getDate();
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();
    return `${month} ${day}, ${year}`;
}


// Populate the table on page load
$(document).ready(function () {
    $.ajax({
        url: '/api/esim/user/plans/',
        type: 'GET',
        success: function (response) {
            console.log(response);
            populateEsimsTable(response);
        }
    });

});