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
    const $tableBody = $("#esims-table-body");
    $tableBody.empty(); // Clear any existing rows

    esims.forEach((esim) => {
        const row = `
        <tr>
          <td>${esim.plan}</td>
          <td><span class="badge ${esim.status === "In Use" ? "bg-label-success" : "bg-label-warning"
            }">${esim.status}</span></td>
          <td>≈ ${esim.dataLeft.gb}GB (${esim.dataLeft.percentage}%)</td>
          <td>${esim.timeLeft.days} days ${esim.timeLeft.hours} hours</td>
          <td>${formatDate(esim.activateBefore)}</td>
          <td>${esim.iccid}</td>
        </tr>
      `;

        $tableBody.append(row);
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
        url: '/api/payments/',
        type: 'GET',
        success: function (response) {
            console.log(response);
            populateEsimsTable(response);
        }
    });

    $(document).on('click', '.confirm-payment-btn', function (e) {
        const ref_id = $(this).data("ref_id");

        var submitButton = $(this);
        submitButton.html('<span class="spinner-border m-2 mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

        $.ajax({
            url: `/api/payments/status/${ref_id}/`,
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            success: function (response) {
                console.log(response.message);
                showToast(response.message, 'bg-success');
                location.reload();
            },
            error: function (error) {
                console.error(error);
                if (error.responseJSON.message.error !== undefined) {
                    showToast(error.responseJSON.message.error, 'bg-danger');
                } else {
                    showToast('Server error! Try again later.', 'bg-danger');
                }
            },
            complete: function () {
                // Revert button text and re-enable the button
                submitButton.html('Confirm Payment').attr('disabled', false);
            }
        });
    });

});