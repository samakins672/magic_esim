// Handle Personal Form submission
$(document).on('submit', '#userAuth', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    email = $('#userAuth [name="email"]').val();
    phone_number = $('#userAuth [name="phone_number"]').val();

    var formData = JSON.stringify({
        first_name: $('#userAuth [name="first_name"]').val(),
        last_name: $('#userAuth [name="last_name"]').val(),
        email: email,
        phone_number: phone_number,
        password: $('#userAuth [name="password"]').val(),
        referral_code: $('#userAuth [name="referral_code"]').val()
    });

    $.ajax({
        url: '/api/auth/register/',
        method: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            showToast(response.message, 'bg-success');
            
            $('.user_email').text(email);
            $('#otpVerifyForm [name="email"]').val(email);
            $('#otpVerifyForm [name="phone_number"]').val(phone_number);

            // Open modal on success
            $('#verificationModal').modal('show');
        },
        error: function (error) {
            console.error(error);
            showToast("User with this email or phone number already exists", 'bg-danger');
        },
        complete: function() {
            // Revert button text and re-enable the button
            submitButton.html('Submit changes').attr('disabled', false);
        }
    });
});

$(document).on('submit', '#signInForm', function (e) {
    e.preventDefault();

    // Get the button element
    var submitButton = $('#submitBtn');

    // Change button text to spinner
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    var formData = JSON.stringify({
        email: $('#signInForm [name="email"]').val(),
        password: $('#signInForm [name="password"]').val()
    });

    $.ajax({
        url: '/api/auth/login/',
        type: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            // On success, show success message
            showToast('Log In successful!', 'bg-success');
            console.log('Log In successfully:', response);

            // Redirect to dashboard after login success
            window.location.href = '/dashboard';
        },
        error: function (error) {
            // On error, show error message
            showToast(error, 'bg-danger');
        },
        complete: function () {
            // Revert button text and re-enable the button
            submitButton.html('Log in').attr('disabled', false);
        }
    });
});

$(document).on('submit', '#otpVerifyForm', function (e) {
    e.preventDefault();

    // Get the button element
    var submitButton = $('#confirm-btn');

    // Change button text to spinner
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    const code = $('.code-input').map(function () {
        return $(this).val();
    }).get().join('');
    
    var formData = JSON.stringify({
        email: $('#otpVerifyForm [name="email"]').val(),
        phone_number: $('#otpVerifyForm [name="phone_number"]').val(),
        otp: code,
    });

    $.ajax({
        url: '/api/auth/otp/verify/',
        type: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            showToast(response.message, 'bg-success');

            // Redirect to login after verification is successful
            window.location.href = '/login';
        },
        error: function (error) {
            // On error, show error message
            showToast(error, 'bg-danger');
        },
        complete: function () {
            // Revert button text and re-enable the button
            submitButton.html('Confirm').attr('disabled', false);
        }
    });
});