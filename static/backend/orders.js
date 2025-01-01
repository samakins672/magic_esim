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
          data-esim_plan="${order.esim_plan}"
          data-bs-toggle="modal" 
          data-bs-target="#orderDetailsModal">
          <i class="bx bx-show"></i>
        </button>`;

        const confirmPaymentButton = `
        <button class="btn btn-success btn-sm confirm-payment-btn" 
          data-id="${order.ref_id}" 
          data-payment_url="${order.payment_url}">
          Confirm Payment
        </button>`;

        const expiryCountdown =
            expiryTime && expiryTime > 0
                ? `<span class="countdown-timer" data-id="${order.id}">${expiryTime}s</span>` :
            order.status == "COMPLETED" ? `<span class="text-success">Done</span>` : `<span class="text-danger">Exp.</span>`;

        const row = `
        <tr>
          <td>${truncateText(order.gateway_transaction_id, 10)}</td>
          <td class="text-primary">${order.price} ${order.currency}</td>
          <td>${formatDateTime(order.date_created)}</td>
          <td><span class="badge ${order.status === "PENDING" ? "bg-label-warning" : order.status === "FAILED" ?  "bg-label-danger" : "bg-label-success"}">${order.status}</span></td>
          <td>${expiryCountdown}</td>
          <td>
            ${viewDetailsButton}
            ${order.status === "PENDING" ? confirmPaymentButton : ""}
          </td>
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
    const date_created = $(this).data("date_created");
    const expiry_datetime = $(this).data("expiry_datetime");
    const esim_plan = $(this).data("esim_plan");

    // Populate modal with order details
    $("#modal-order-id").text(gateway_transaction_id);
    $("#modal-order-status")
        .text(status)
        .removeClass("bg-label-success bg-label-warning bg-label-danger")
        .addClass(status === "PENDING" ? "bg-label-warning" : status === "FAILED" ?  "bg-label-danger" : "bg-label-success");
    $("#modal-order-price").text(`${price} ${currency}`);
    $("#modal-payment-gateway").text(payment_gateway);
    $("#modal-date-created").text(formatDateTime(date_created));
    $("#modal-expiry-date").text(formatDateTime(expiry_datetime));
    $("#modal-date-paid").text(status === "COMPLETED" ? `${formatDateTime(date_paid)}` : "N/A");
    $("#modal-esim-plan").text(esim_plan);
    $("#modal-payment-url").attr("href", payment_url);
});

// Function to calculate time difference
function getCountdown(expiryDate) {
    const now = new Date().getTime();
    const expiry = new Date(expiryDate).getTime();
    const diff = expiry - now;
    return diff > 0 ? diff : 0;
}

// Function to start countdown
function startCountdown(orderId, expiryDate) {
    const $countdownElement = $(`.countdown-timer[data-id="${orderId}"]`);
    const interval = setInterval(() => {
        const remaining = getCountdown(expiryDate);
        if (remaining > 0) {
            const minutes = Math.floor(remaining / 60000);
            const seconds = Math.floor((remaining % 60000) / 1000);
            if (minutes > 0) {
                $countdownElement.text(`${minutes}m ${seconds}s`);
            } else {
                $countdownElement.text(`${seconds}s`);
            }
        } else {
            $countdownElement.text("Exp.").addClass("text-danger");
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
