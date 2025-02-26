$(document).on('submit', '#virtualNumberRequestForm', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

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
            loader.addClass("d-none");
        }
    });
});
