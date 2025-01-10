$(document).on('submit', '#virtualNumberRequestForm', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn1');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    var formData = JSON.stringify({
        full_name: $('#virtualNumberRequestForm [name="full_name"]').val(),
        email: $('#virtualNumberRequestForm [name="email"]').val(),
        nationality: $('#virtualNumberRequestForm [name="nationality"]').val(),
        purpose: $('#virtualNumberRequestForm [name="purpose"]').val(),
        service_country: $('#virtualNumberRequestForm [name="service_country"]').val()
    });

    $.ajax({
        url: '/api/number/request/',
        method: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            if (response.status) {
                showToast(response.message, 'bg-success');
                $('#virtualNumberRequestForm')[0].reset();
            } else {
                showToast(response.message, 'bg-danger');
            }
        },
        error: function (error) {
            console.error(error);
            showToast("Unable to send request, please try again later", 'bg-danger');
        },
        complete: function() {
            // Revert button text and re-enable the button
            submitButton.html('Send Request').attr('disabled', false);
        }
    });
});
