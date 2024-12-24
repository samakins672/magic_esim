window.assetsPath = document.documentElement.getAttribute("data-assets-path"),
window.templateName = document.documentElement.getAttribute("data-template"),
window.rtlSupport = !0,
"undefined" != typeof TemplateCustomizer && (window.templateCustomizer = new TemplateCustomizer({
    cssPath: assetsPath + "vendor/css/",
    themesPath: assetsPath + "vendor/css/",
    displayCustomizer: !0,
    controls: ["rtl", "style"]
}));
