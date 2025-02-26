document.querySelectorAll('.single-open .panel-header').forEach(header => {
    header.addEventListener('click', () => {
        const parent = header.parentElement;
        const container = parent.parentElement;

        container.querySelectorAll('.panel').forEach(panel => {
            if (panel !== parent) panel.classList.remove('active');
        });

        parent.classList.toggle('active');
    });
});