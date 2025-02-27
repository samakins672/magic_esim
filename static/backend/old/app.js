const csrfToken = $('meta[name="csrf-token"]').attr('content');

// Function to show toast
function showToast(message, bgClass) {
    var toastEl = $('#responseToast');
    toastEl.find('.toast-body').text(message); // Set the message
    toastEl.removeClass('bg-primary bg-secondary bg-info bg-success bg-danger').addClass(bgClass); // Add appropriate background class
    var toast = new bootstrap.Toast(toastEl[0]); // Initialize the toast
    toast.show(); // Show the toast
}

// Function to get query parameters from the URL
function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Function to format price with commas
function formatPrice(price) {
    // Ensure price is a number, and handle non-numeric values
    const numericPrice = parseFloat(price);
    if (isNaN(numericPrice)) {
        return 'Invalid price'; // Return a message if the price is invalid
    }

    // Round to two decimal places and format with commas
    const formattedPrice = numericPrice.toFixed(2);
    return parseFloat(formattedPrice).toLocaleString('en-US');
}

// Custom function to format date as '23rd Sept, 2024'
function formatDate(dateString) {
    const date = new Date(dateString);

    const day = date.getDate();
    const daySuffix = getDaySuffix(day);
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"];
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();

    return `${day}${daySuffix} ${month}, ${year}`;
}

// Custom function to format date as '23 Dec. 10:00 PM'
function formatDateTime(dateString) {
    const date = new Date(dateString);

    const day = date.getDate();
    const daySuffix = getDaySuffix(day);
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"];
    const month = monthNames[date.getMonth()];

    // Format time as 12-hour format
    let hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, '0'); // Ensure two-digit minutes
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // Hour '0' should be '12'

    return `${day} ${month}. ${hours}:${minutes} ${ampm}`;
}

// Function to determine the suffix for the day (e.g., 'st', 'nd', 'rd', 'th')
function getDaySuffix(day) {
    if (day > 3 && day < 21) return 'th'; // Suffix 'th' for 4th-20th
    switch (day % 10) {
        case 1: return "st";
        case 2: return "nd";
        case 3: return "rd";
        default: return "th";
    }
}

// Helper function to convert base64 to Blob
function dataURLtoBlob(dataURL) {
    const byteString = atob(dataURL.split(',')[1]);
    const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

// Helper function to map statuses to badge styles and labels
function getStatusBadge(status) {
    switch (status) {
        case 'pending':
            return { class: 'warning', label: 'Pending' };
        case 'investigated':
            return { class: 'info', label: 'Investigated' };
        default:
            return { class: 'success', label: 'Done' };
    }
}

// Function to populate the table with data
function InitiateDatatable(table) {
    // Initialize DataTable after populating the table
    if ($.fn.dataTable.isDataTable(table)) {
        $(table).DataTable().off().destroy(); // Destroy the previous DataTable if it exists
    }

    // Initialize the DataTable with custom settings
    $(table).DataTable({
        searching: true,
        ordering: true,
        paging: true
    });
}

// Function to truncate text to a specified character limit
function truncateText(text, charLimit) {
    // Handle null or undefined text
    if (!text) {
        return "";
    }

    // Ensure the text is truncated if it exceeds the character limit
    if (text.length > charLimit) {
        return text.slice(0, charLimit) + "...";
    }
    return text; // Return the text as-is if it's within the limit
}

// Function to block UI
function blockUI(target) {
    $(target).append(`
      <div class="block-ui-overlay" style="
        width: 100%;
        height: 50vh;
        display: flex;
        justify-content: center;
        align-items: center;">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `);
}

// Function to unblock UI
function unblockUI(target) {
    $(target).find(".block-ui-overlay").remove();
}


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
            const days = Math.floor(remaining / (1000 * 60 * 60 * 24));
            const hours = Math.floor((remaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
            let countdownText = '';
            if (days > 0) {
                countdownText += `${days}d `;
            }
            if (hours > 0 || days > 0) {
                countdownText += `${hours}h `;
            }
            if (minutes > 0 || hours > 0 || days > 0) {
                countdownText += `${minutes}m `;
            }
            countdownText += `${seconds}s`;
            $countdownElement.text(countdownText);
        } else {
            $countdownElement.text("Exp.").addClass("text-danger");
            clearInterval(interval); // Stop the timer
        }
    }, 1000);
}

/**
 * Calculate remaining duration based on created date, duration, and current date.
 * @param {string} dateCreated - The creation date of the plan (ISO string).
 * @param {number} duration - The duration of the plan in days.
 * @returns {object} - An object with `isExpired`, `durationLeft`, `expiryDate`, and `remainingDaysHours`.
 */
function calculateRemainingDuration(dateCreated, duration) {
    // Parse the created date
    const createdDate = new Date(dateCreated);

    // Calculate expiry date
    const durationInMs = duration * 24 * 60 * 60 * 1000; // Duration in milliseconds
    const expiryDate = new Date(createdDate.getTime() + durationInMs);

    // Get current date
    const now = new Date();

    // Check if expired
    const isExpired = now > expiryDate;

    // Calculate remaining time
    const timeLeftMs = isExpired ? 0 : expiryDate - now; // Remaining time in milliseconds
    const durationLeftDays = Math.floor(timeLeftMs / (24 * 60 * 60 * 1000)); // Remaining days
    const remainingHours = Math.floor(
        (timeLeftMs % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000)
    ); // Remaining hours

    // Format duration left
    const durationLeft = isExpired
        ? "Expired"
        : `${durationLeftDays} Day${durationLeftDays !== 1 ? "s" : ""}${remainingHours > 0
            ? ` ${remainingHours} Hour${remainingHours !== 1 ? "s" : ""}`
            : ""
        }`;

    // Return calculated details
    return {
        isExpired,
        durationLeft,
        expiryDate: expiryDate.toISOString(),
        remainingDaysHours: {
            days: durationLeftDays,
            hours: remainingHours,
        },
    };
}

// Define a function to map status to badge color
function getBadgeColor(esimStatus) {
    switch (esimStatus) {
        case "CREATE":
            return "bg-label-primary"; // Blue
        case "PAYING":
            return "bg-label-warning"; // Yellow
        case "PAID":
            return "bg-label-info"; // Light Blue
        case "GETTING_RESOURCE":
            return "bg-label-secondary"; // Grey
        case "GOT_RESOURCE":
            return "bg-label-success"; // Green
        case "IN_USE":
            return "bg-label-success"; // Green
        case "USED_UP":
            return "bg-label-danger"; // Red
        case "UNUSED_EXPIRED":
            return "bg-label-dark"; // Black
        case "USED_EXPIRED":
            return "bg-label-dark"; // Black
        case "CANCEL":
            return "bg-label-danger"; // Red
        case "SUSPENDED":
            return "bg-label-warning"; // Yellow
        case "REVOKE":
            return "bg-label-danger"; // Red
        default:
            return "bg-label-secondary"; // Grey (default)
    }
}

// Helper functions for formatting data
function formatVolume(bytes) {
    return bytes < 1024 ** 3
        ? `${(bytes / (1024 ** 2)).toFixed(0)} MB`
        : `${(bytes / (1024 ** 3)).toFixed(1)} GB`;
}

function calculateTimeLeft(expiredTime) {
    const now = new Date();
    const expiryDate = new Date(expiredTime);
    const diffTime = Math.max(expiryDate - now, 0);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 1 ? `${diffDays} Days` : `${diffDays} Day`;
}