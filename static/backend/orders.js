// Example API response with `payment_url`
const apiResponse = [
    {
        id: 40,
        price: "10.00",
        currency: "USD",
        payment_gateway: "CoinPayments",
        payment_method: "CARD",
        status: "PENDING",
        expiry_datetime: "2025-12-31T12:00:00.000Z",
        payment_url: "https://example.com/payment/40",
    },
    {
        id: 41,
        price: "10.00",
        currency: "USD",
        payment_gateway: "CoinPayments",
        payment_method: "CARD",
        status: "COMPLETED",
        expiry_datetime: "2024-12-31T12:30:00.000Z",
        payment_url: "https://example.com/payment/41",
    },
];

// Function to populate the table
function populateOrdersTable(orders) {
    const $tableBody = $("#orders-table-body");
    $tableBody.empty(); // Clear existing rows

    // Sort orders by date_created
    orders.sort((a, b) => new Date(b.date_created) - new Date(a.date_created));

    orders.forEach((order) => {
        const expiryTime = order.expiry_datetime
            ? getCountdown(order.expiry_datetime)
            : null;

        const viewDetailsButton = `
        <button class="btn btn-primary btn-sm view-details-btn" 
          data-id="${order.id}" 
          data-gateway_transaction_id="${order.gateway_transaction_id}" 
          data-price="${order.price}" 
          data-currency="${order.currency}" 
          data-payment_address="${order.payment_address}" 
          data-payment_gateway="${order.payment_gateway}" 
          data-payment_url="${order.payment_url}" 
          data-status="${order.status}" 
          data-date_paid="${order.date_paid}" 
          data-ref_id="${order.ref_id}"
          data-date_created="${order.date_created}"
          data-expiry_datetime="${order.expiry_datetime}"
          data-bs-toggle="modal" 
          data-bs-target="#orderDetailsModal">
          View Details
        </button>`;

        const expiryCountdown =
            expiryTime && expiryTime > 0
                ? `<span class="countdown-timer" data-id="${order.id}">${expiryTime}s</span>`
                : `<span class="text-danger">Expired</span>`;

        const row = `
        <tr>
          <td>${truncateText(order.gateway_transaction_id, 10)}</td>
          <td class="text-primary">${order.price} ${order.currency}</td>
          <td>${formatDateTime(order.date_created)}</td>
          <td><span class="badge ${order.status === "PENDING" ? "bg-warning" : "bg-success"
            }">${order.status}</span></td>
          <td>${expiryCountdown}</td>
          <td>${viewDetailsButton}</td>
        </tr>
      `;

        $tableBody.append(row);

        // Start a countdown timer for active expiry times
        if (expiryTime && expiryTime > 0) {
            startCountdown(order.id, order.expiry_datetime);
        }
    });
}

// Function to open modal and populate order details
$(document).on("click", ".view-details-btn", function () {
    const orderId = $(this).data("id");
    const gateway_transaction_id = $(this).data("gateway_transaction_id");
    const price = $(this).data("price");
    const currency = $(this).data("currency");
    const payment_address = $(this).data("payment_address");
    const payment_url = $(this).data("payment_url");
    const payment_gateway = $(this).data("payment_gateway");
    const status = $(this).data("status");
    const date_paid = $(this).data("date_paid");
    const ref_id = $(this).data("ref_id");
    const date_created = $(this).data("date_created");
    const expiry_datetime = $(this).data("expiry_datetime");

    // Populate modal with order details
    $("#modal-order-id").text(gateway_transaction_id);
    $("#modal-order-status")
        .text(status)
        .removeClass("bg-success bg-warning")
        .addClass(status === "PENDING" ? "bg-warning" : "bg-success");
    $("#modal-order-price").text(`${price} ${currency}`);
    $("#modal-payment-gateway").text(payment_gateway);
    $("#modal-expiry-date").text(formatDateTime(expiry_datetime));
    $("#modal-payment-method").text(payment_method);
    $("#modal-payment-url").attr("href", payment_url);
});

// Function to calculate time difference
function getCountdown(expiryDate) {
    const now = new Date().getTime();
    const expiry = new Date(expiryDate).getTime();
    const diff = expiry - now;
    return diff > 0 ? Math.floor(diff / 1000) : 0;
}

// Function to start countdown
function startCountdown(orderId, expiryDate) {
    const $countdownElement = $(`.countdown-timer[data-id="${orderId}"]`);
    const interval = setInterval(() => {
        const remaining = getCountdown(expiryDate);
        if (remaining > 0) {
            $countdownElement.text(`${remaining}s`);
        } else {
            $countdownElement.text("Expired").addClass("text-danger");
            clearInterval(interval); // Stop the timer
        }
    }, 1000);
}

// Populate the table on page load
$(document).ready(function () {
    $.ajax({
        url: '/api/payments/',
        type: 'GET',
        success: function (response) {
            console.log(response);
            populateOrdersTable(response);
        }
    });

});
