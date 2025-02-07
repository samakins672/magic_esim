// Handle Personal Form submission
$(document).on('submit', '#userAuth', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    email = $('#userAuth [name="email"]').val();

    var formData = JSON.stringify({
        first_name: $('#userAuth [name="first_name"]').val(),
        last_name: $('#userAuth [name="last_name"]').val(),
        email: email,
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

            // Open modal on success
            $('#verificationModal').modal('show');
        },
        error: function (error) {
            console.error(error);
            showToast("User with this email already exists", 'bg-danger');
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
            // On error show error message
            if (error.responseJSON.message.error !== undefined) {
                showToast(error.responseJSON.message.error, 'bg-danger');
            } else {
                showToast('Invalid email or password', 'bg-danger');
            }
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
            // On error show error message
            if (error.responseJSON.message.error !== undefined) {
                showToast(error.responseJSON.message.error, 'bg-danger');
            } else {
                showToast('Server error! Try again later.', 'bg-danger');
            }
        },
        complete: function () {
            // Revert button text and re-enable the button
            submitButton.html('Confirm').attr('disabled', false);
        }
    });
});

$(document).on('submit', '#formAccountSettings', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    var formData = new FormData(this);

    // Check if a file is selected
    var profileImageInput = $('#upload')[0];
    if (profileImageInput.files.length === 0) {
        formData.delete('profile_image');
    }

    $.ajax({
        url: '/api/auth/user/me/',
        method: 'PATCH',
        processData: false,
        contentType: false,
        data: formData,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            showToast(response.message, 'bg-success');
            location.reload();
        },
        error: function (error) {
            console.error(error);
            showToast("User with this email already exists", 'bg-danger');
        },
        complete: function() {
            // Revert button text and re-enable the button
            submitButton.html('Submit changes').attr('disabled', false);
        }
    });
});

$(document).on('submit', '#formChangePassword', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn2');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    new_password = $('#formChangePassword [name="new_password"]').val();
    confirm_password = $('#formChangePassword [name="confirm_password"]').val();

    $('#changePasswordForm [name="new_password"]').val(new_password);
    $('#changePasswordForm [name="confirm_password"]').val(confirm_password);

    $('#changePasswordModal').modal('show');
});

$(document).on('submit', '#changePasswordForm', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn3');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    var formData = JSON.stringify({
        old_password: $('#changePasswordForm [name="old_password"]').val(),
        new_password: $('#changePasswordForm [name="new_password"]').val(),
        confirm_password: $('#changePasswordForm [name="confirm_password"]').val(),
    });

    $.ajax({
        url: '/api/auth/password/change/',
        method: 'POST',
        data: formData,
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
        complete: function() {
            // Revert button text and re-enable the button
            submitButton.html('Submit changes').attr('disabled', false);
        }
    });
});
