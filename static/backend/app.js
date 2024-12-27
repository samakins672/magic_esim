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
    
    return `${day}${daySuffix} ${month}, ${hours}:${minutes} ${ampm}`;
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
