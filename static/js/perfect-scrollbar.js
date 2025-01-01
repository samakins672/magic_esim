document.addEventListener("DOMContentLoaded", function() {
    var e, t, l;
    e = document.getElementById("vertical-scroll_bar"),
    t = document.getElementById("horizontal-scroll_bar"),
    l = document.getElementById("both-scrollbars-scroll_bar"),
    e && new PerfectScrollbar(e,{
        wheelPropagation: !1
    }),
    t && new PerfectScrollbar(t,{
        wheelPropagation: !1,
        suppressScrollY: !0
    }),
    l && new PerfectScrollbar(l,{
        wheelPropagation: !1
    })
});
