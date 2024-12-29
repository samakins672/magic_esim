document.addEventListener("DOMContentLoaded", function(e) {
  {
      let e = document.querySelector("#formAccountSettings")
        , t = document.querySelector("#formAccountDeactivation")
        , n = t.querySelector(".deactivate-account")
        , o = (e && FormValidation.formValidation(e, {
          fields: {
              first_name: {
                  validators: {
                      notEmpty: {
                          message: "Please enter first name"
                      }
                  }
              },
              last_name: {
                  validators: {
                      notEmpty: {
                          message: "Please enter last name"
                      }
                  }
              }
          },
          plugins: {
              trigger: new FormValidation.plugins.Trigger,
              bootstrap5: new FormValidation.plugins.Bootstrap5({
                  eleValidClass: "",
                  rowSelector: ".col-md-6"
              }),
              autoFocus: new FormValidation.plugins.AutoFocus
          },
          init: e => {
              e.on("plugins.message.placed", function(e) {
                  e.element.parentElement.classList.contains("input-group") && e.element.parentElement.insertAdjacentElement("afterend", e.messageElement)
              })
          }
      }),
      t && FormValidation.formValidation(t, {
          fields: {
              accountActivation: {
                  validators: {
                      notEmpty: {
                          message: "Please confirm you want to delete account"
                      }
                  }
              }
          },
          plugins: {
              trigger: new FormValidation.plugins.Trigger,
              bootstrap5: new FormValidation.plugins.Bootstrap5({
                  eleValidClass: ""
              }),
              submitButton: new FormValidation.plugins.SubmitButton,
              fieldStatus: new FormValidation.plugins.FieldStatus({
                  onStatusChanged: function(e) {
                      e ? n.removeAttribute("disabled") : n.setAttribute("disabled", "disabled")
                  }
              }),
              autoFocus: new FormValidation.plugins.AutoFocus
          },
          init: e => {
              e.on("plugins.message.placed", function(e) {
                  e.element.parentElement.classList.contains("input-group") && e.element.parentElement.insertAdjacentElement("afterend", e.messageElement)
              })
          }
      }),
      document.querySelector("#accountActivation"));
      n && (n.onclick = function() {
          1 == o.checked && Swal.fire({
          text: "Are you sure you would like to deactivate your account?",
          icon: "warning",
          showCancelButton: !0,
          confirmButtonText: "Yes",
          customClass: {
          confirmButton: "btn btn-primary me-2",
          cancelButton: "btn btn-label-secondary"
          },
          buttonsStyling: !1
          }).then(function(e) {
          if (e.value) {
          fetch('/api/auth/user/me/', {
              method: 'DELETE',
              headers: {
              'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
              }
          })
          .then(response => {
              if (response.status === 204) {
              Swal.fire({
              icon: "success",
              title: "Deleted!",
              text: "Your account has been deactivated.",
              customClass: {
                  confirmButton: "btn btn-success"
              }
              }).then(() => {
                  window.location.href = '/';
              });
              } else {
              response.json().then(data => {
                  Swal.fire({
                  icon: "error",
                  title: "Error!",
                  text: data.message || "There was an error deactivating your account.",
                  customClass: {
                      confirmButton: "btn btn-danger"
                  }
                  });
              });
              }
          })
          .catch(error => {
              Swal.fire({
              icon: "error",
              title: "Error!",
              text: "There was an error deactivating your account.",
              customClass: {
              confirmButton: "btn btn-danger"
              }
              });
          });
          } else if (e.dismiss === Swal.DismissReason.cancel) {
          Swal.fire({
              title: "Cancelled",
              text: "Deactivation Cancelled!!",
              icon: "error",
              customClass: {
              confirmButton: "btn btn-success"
              }
          });
          }
          });
      });
      let a = document.getElementById("uploadedAvatar")
        , i = document.querySelector(".account-file-input")
        , l = document.querySelector(".account-image-reset");
      if (a) {
          let e = a.src;
          i.onchange = () => {
              i.files[0] && (a.src = window.URL.createObjectURL(i.files[0]))
          }
          ,
          l.onclick = () => {
              i.value = "",
              a.src = e
          }
      }
  }
}),
$(function() {
  var e = $(".select2");
  e.length && e.each(function() {
      var e = $(this);
      e.wrap('<div class="position-relative"></div>'),
      e.select2({
          dropdownParent: e.parent()
      })
  })
});
