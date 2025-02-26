const bottomBar = document.querySelector('.bottomBar')

function openSidebar(){
    bottomBar.style.transform = "translateY(0%)";
}

function closeSidebar(){
    bottomBar.style.transform = "translateY(127%)";
}