
// Handle Personal Form submission
$(document).on('submit', '#userAuth', function (e) {
    e.preventDefault();

    var submitButton = $('#submitBtn2');
    submitButton.html('<span class="spinner-border mx-auto" role="status" aria-hidden="true"></span>').attr('disabled', true);

    // Create a FormData object to gather form data
    var formData = new FormData(this);

    var password = formData.get('password');
    formData.append('re_password', password);

    // Check if a file is selected
    var profileImageInput = $('#profileImage')[0];
    if (profileImageInput.files.length === 0) {
        // If no file is selected, remove the profile_image field from the FormData
        formData.delete('profile_image');
    }

    $.ajax({
        url: `${mainURL}/api/users/`,
        method: 'POST',
        processData: false,
        contentType: false,
        data: formData,
        success: function (response) {
            console.log('Sign In successfully:', response);
            showToast('Your account has been created successful!', 'bg-success');

            $('#userAuth').slideUp('fast', function () {
                $('.message').slideDown('fast');
            });
        },
        error: function (error) {
            showToast('User with email address already exists!', 'bg-danger');
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
        contentType: 'application/json',
        success: function (response) {
            // On success, show success message
            showToast('Log In successful!', 'bg-success');
            console.log('Log In successfully:', response);

            // Redirect to dashboard after login success
            window.location.href = '/dashboard';
        },
        error: function (error) {
            // On error, show error message
            showToast(error.responseJSON?.detail || 'An error occurred.', 'bg-danger');
            console.log('Error:', error.responseJSON.detail);
        },
        complete: function () {
            // Revert button text and re-enable the button
            submitButton.html('Log in').attr('disabled', false);
        }
    });
});