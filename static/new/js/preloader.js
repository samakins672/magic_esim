const preloader = document.querySelector('.preloader');

function preload() {
    preloader.style.transition = "opacity 0.5s ease";
    preloader.style.opacity = "0";

    setTimeout(() => {
        preloader.style.display = "none";
    }, 500);
}
