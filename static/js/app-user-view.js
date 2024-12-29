!function() {
    let e = document.querySelector("#formChangePassword");
    e && FormValidation.formValidation(e, {
        fields: {
            new_password: {
                validators: {
                    notEmpty: {
                        message: "Please enter new password"
                    },
                    stringLength: {
                        min: 8,
                        message: "Password must be more than 8 characters"
                    }
                }
            },
            confirm_password: {
                validators: {
                    notEmpty: {
                        message: "Please confirm new password"
                    },
                    identical: {
                        compare: function() {
                            return e.querySelector('[name="new_password"]').value
                        },
                        message: "The password and its confirm are not the same"
                    },
                    stringLength: {
                        min: 8,
                        message: "Password must be more than 8 characters"
                    }
                }
            }
        },
        plugins: {
            trigger: new FormValidation.plugins.Trigger,
            bootstrap5: new FormValidation.plugins.Bootstrap5({
                eleValidClass: "",
                rowSelector: ".form-password-toggle"
            }),
            autoFocus: new FormValidation.plugins.AutoFocus
        },
        init: e => {
            e.on("plugins.message.placed", function(e) {
                e.element.parentElement.classList.contains("input-group") && e.element.parentElement.insertAdjacentElement("afterend", e.messageElement)
            })
        }
    })
}();
