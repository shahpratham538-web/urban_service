document.addEventListener("DOMContentLoaded", () => {
    // Subtle table hover effects are handled by CSS, but we can add JS interactions
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        // Remove border attributes added directly to HTML to let CSS take over
        table.removeAttribute('border');
        table.removeAttribute('cellpadding');
        table.removeAttribute('cellspacing');
    });

    // Hide sidebar on auth screens if not logged in
    const isAuth = window.APP_CONTEXT && window.APP_CONTEXT.isAuthenticated;
    if (!isAuth) {
        const sidebar = document.getElementById('appSidebar');
        if (sidebar && (window.location.pathname.includes('/login/') || 
            window.location.pathname.includes('/signup/') || 
            window.location.pathname.includes('/password-reset/'))) {
            sidebar.style.display = 'none';
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.style.maxWidth = '700px';
                mainContent.style.margin = '5vh auto';
            }
            const pageHeader = document.querySelector('.page-header');
            if (pageHeader) pageHeader.style.display = 'none';
            
            // Add a welcome header to the auth card
            const contentCard = document.querySelector('.content-card');
            if (contentCard) {
                const title = document.createElement('h2');
                title.style.color = '#4f46e5';
                title.style.textAlign = 'center';
                title.style.marginBottom = '30px';
                title.style.fontWeight = '800';
                title.innerText = 'Urban Service Platform';
                contentCard.prepend(title);
            }
        }
    }

    // Auto-fade messages
    const messageContainer = document.querySelector('.messages');
    if (messageContainer) {
        setTimeout(() => {
            messageContainer.style.transition = 'opacity 0.6s ease';
            messageContainer.style.opacity = '0';
            setTimeout(() => messageContainer.remove(), 600);
        }, 6000);
    }
});
