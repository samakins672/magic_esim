document.addEventListener('DOMContentLoaded', () => {
    const codeInputs = document.querySelectorAll('.code-input');

    codeInputs.forEach((input, index) => {
        // Enforce single-digit rule
        input.addEventListener('input', (e) => {
            // Handle pasting data into the input
            if (e.inputType === 'insertFromPaste') {
                const pastedData = e.target.value.trim();
                if (pastedData.length <= codeInputs.length) {
                    pastedData.split('').forEach((char, i) => {
                        if (codeInputs[i]) {
                            codeInputs[i].value = char[0];
                        }
                    });
                    const lastFilledInput = codeInputs[Math.min(pastedData.length - 1, codeInputs.length - 1)];
                    if (lastFilledInput) {
                        lastFilledInput.focus(); // Focus on the last filled box
                    }
                }
            } else if (input.value.length === 1 && index < codeInputs.length - 1) {
                codeInputs[index + 1].focus(); // Move to the next input
            }
            
            if (input.value.length > 1) {
                input.value = input.value[0]; // Keep only the first digit
            }
        });

        // Handle backspace to move focus to the previous input
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace') {
                if (input.value.length === 0 && index > 0) {
                    codeInputs[index - 1].focus(); // Move to the previous input
                }
            }
        });
    });

    // Resend timer logic
    let timer = 60;
    const timerElement = document.getElementById('resend-timer');
    const updateTimer = () => {
        timer--;
        timerElement.textContent = `Resend in ${timer}secs`;
        if (timer === 0) {
            clearInterval(interval);
            timerElement.textContent = 'Resend Code';
            timerElement.style.cursor = 'pointer';
        }
    };

    const interval = setInterval(updateTimer, 1000);

    // Resend click handler
    timerElement.addEventListener('click', () => {
        if (timer === 0) {
            timer = 60;
            timerElement.textContent = `Resend in ${timer}secs`;
            timerElement.style.cursor = 'default';

            const newInterval = setInterval(() => {
                updateTimer();
                if (timer === 0) {
                    clearInterval(newInterval);
                }
            }, 1000);

            var formData = JSON.stringify({
                email: document.querySelector('#otpVerifyForm [name="email"]').value,
                phone_number: document.querySelector('#otpVerifyForm [name="phone_number"]').value
            });
        
            fetch('/api/auth/otp/request/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                showToast(data.message, 'bg-success');
            })
            .catch(error => {
                // On error show error message
                if (error.responseJSON.message !== undefined) {
                    message = error.responseJSON.message;
                } else {
                    message = 'Invalid OTP';
                }
                $('.formAlert').removeClass('d-none').text(message);
            })

            // alert('Verification code resent!');
        }
    });
});
