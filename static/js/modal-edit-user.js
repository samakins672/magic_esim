$(function() {
    var e = $(".select2");
    e.length && e.each(function() {
        var e = $(this);
        e.wrap('<div class="position-relative"></div>').select2({
            placeholder: "Select value",
            dropdownParent: e.parent()
        })
    })
});