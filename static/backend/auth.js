// Handle Personal Form submission
$(document).on('submit', '#userAuth', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

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
            
            // Redirect to verification after signup success
            window.location.href = '/verify/' + email;
        },
        error: function (error) {
            console.error(error);
            $('.formAlert').removeClass('d-none').text("User with this email already exists.");
        },
        complete: function() {
            loader.addClass("d-none");
        }
    });
});

$(document).on('submit', '#formAuthentication', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

    email = $('#formAuthentication [name="email"]').val();

    var formData = JSON.stringify({
        email: email
    });

    $.ajax({
        url: '/api/auth/password/reset/',
        method: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            
            // Redirect to verification with password-reset flow indicator
            window.location.href = '/verify/' + email + '?flow=password-reset';
        },
        error: function (error) {
            console.error(error);
            $('.formAlert').removeClass('d-none').text("User with this email doesn't exist.");
        },
        complete: function() {
            loader.addClass("d-none");
        }
    });
});

$(document).on('submit', '#signInForm', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

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
            console.log('Log In successfully:', response);

            const urlParams = new URLSearchParams(window.location.search);
            const next = urlParams.get('next');
            if (next) {
                window.location.href = next;
            } else {
                window.location.href = '/';
            }
        },
        error: function (error) {
            // On error show error message
            if (error.responseJSON.message.error !== undefined) {
                message = error.responseJSON.message.error;
            } else {
                message = 'Invalid email or password';
            }
            $('.formAlert').removeClass('d-none').text(message);
        },
        complete: function () {
            loader.addClass("d-none");
        }
    });
});

$(document).on('submit', '#otpVerifyForm', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

    const code = $('.code-input').map(function () {
        return $(this).val();
    }).get().join('');
    
    const email = $('#otpVerifyForm [name="email"]').val();
    
    // Check if this is a password reset flow
    const urlParams = new URLSearchParams(window.location.search);
    const flow = urlParams.get('flow');
    const isPasswordReset = flow === 'password-reset';
    
    if (isPasswordReset) {
        // For password reset, just validate OTP and redirect to password reset confirmation
        // We don't call the verify endpoint because we don't want to log the user in yet
        var formData = JSON.stringify({
            email: email,
            otp: code,
        });

        // Validate the OTP exists but don't verify it yet (we'll verify during password reset)
        // Instead, redirect directly to password reset confirmation with OTP
        window.location.href = '/reset-password/confirm/' + encodeURIComponent(email) + '/' + code;
        
    } else {
        // For signup verification, use the existing flow
        var formData = JSON.stringify({
            email: email,
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

                // Redirect to login after verification is successful
                window.location.href = '/login';
            },
            error: function (error) {
                // On error show error message
                if (error.responseJSON.message !== undefined) {
                    message = error.responseJSON.message;
                } else {
                    message = 'Invalid OTP';
                }
                $('.formAlert').removeClass('d-none').text(message);
            },
            complete: function () {
                loader.addClass("d-none");
            }
        });
    }
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

$(document).on('submit', '#passwordResetConfirmForm', function (e) {
    e.preventDefault();

    loader = $('.loading');
    loader.removeClass("d-none");

    var formData = JSON.stringify({
        email: $('#passwordResetConfirmForm [name="email"]').val(),
        otp: $('#passwordResetConfirmForm [name="otp"]').val(),
        new_password: $('#passwordResetConfirmForm [name="new_password"]').val(),
        confirm_password: $('#passwordResetConfirmForm [name="confirm_password"]').val(),
    });

    $.ajax({
        url: '/api/auth/password/reset/confirm/',
        method: 'POST',
        data: formData,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        success: function (response) {
            console.log(response.message);
            // Show success message briefly, then redirect to login
            $('.formAlert').removeClass('d-none').css('color', 'green').text('Password reset successfully! Redirecting to login...');
            setTimeout(function() {
                window.location.href = '/login';
            }, 2000);
        },
        error: function (error) {
            console.error(error);
            let message = 'Password reset failed.';
            if (error.responseJSON && error.responseJSON.message) {
                if (typeof error.responseJSON.message === 'string') {
                    message = error.responseJSON.message;
                } else if (error.responseJSON.message.error) {
                    message = error.responseJSON.message.error;
                }
            }
            $('.formAlert').removeClass('d-none').css('color', 'red').text(message);
        },
        complete: function() {
            loader.addClass("d-none");
        }
    });
});
