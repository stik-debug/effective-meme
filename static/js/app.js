// Chama App Kenya - Client JS

// Service Worker registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('SW registration failed:', err));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Dark mode toggle
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const html = document.documentElement;

    // Load saved theme
    const savedTheme = localStorage.getItem('chama-theme') || 'light';
    if (savedTheme === 'dark') {
        html.setAttribute('data-bs-theme', 'dark');
        if (themeIcon) themeIcon.className = 'bi bi-sun';
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = html.getAttribute('data-bs-theme');
            if (current === 'dark') {
                html.removeAttribute('data-bs-theme');
                localStorage.setItem('chama-theme', 'light');
                if (themeIcon) themeIcon.className = 'bi bi-moon-stars';
            } else {
                html.setAttribute('data-bs-theme', 'dark');
                localStorage.setItem('chama-theme', 'dark');
                if (themeIcon) themeIcon.className = 'bi bi-sun';
            }
        });
    }

    // Format number inputs on focus
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('focus', function() {
            this.select();
        });
    });
});
