document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const header = document.querySelector('.header');
    const chatArea = document.querySelector('.chat-area');
    const inputArea = document.querySelector('.input-area');

    // Initial setup - sidebar visible on desktop, hidden on mobile
    if (sidebar) {
        if (window.innerWidth <= 480) {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }
    }
    if (hamburgerMenu) {
        hamburgerMenu.style.display = window.innerWidth <= 480 ? 'flex' : 'none';
    }

    // Toggle sidebar function
    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        
        if (sidebar.classList.contains('collapsed')) {
            // When sidebar is collapsed
            if (toggleBtn) toggleBtn.style.display = 'none';
            if (hamburgerMenu) hamburgerMenu.style.display = 'flex';
            
            // Adjust header and chat area when sidebar is collapsed
            if (header) header.style.left = '0';
            if (header) header.style.width = '100%';
            if (chatArea) chatArea.style.marginLeft = '0';
            if (chatArea) chatArea.style.width = '100%';
            if (inputArea) inputArea.style.marginLeft = '0';
            if (inputArea) inputArea.style.width = '100%';
        } else {
            // When sidebar is expanded
            if (toggleBtn) toggleBtn.style.display = 'flex';
            if (hamburgerMenu) hamburgerMenu.style.display = 'none';
            
            // Reset header and chat area to original position
            if (header) header.style.left = '250px';
            if (header) header.style.width = 'calc(100% - 250px)';
            if (chatArea) chatArea.style.marginLeft = '250px';
            if (chatArea) chatArea.style.width = 'calc(100% - 250px)';
            if (inputArea) inputArea.style.left = 'calc(50% + clamp(5px, 12.5vw, 1px))';
            if (inputArea) inputArea.style.width = '85%';
            if (inputArea) inputArea.style.right = '0';
            
            // Adjust for mobile screens
            if (window.innerWidth <= 768) {
                if (header) header.style.left = '180px';
                if (header) header.style.width = 'calc(100% - 180px)';
                if (chatArea) chatArea.style.marginLeft = '180px';
                if (chatArea) chatArea.style.width = 'calc(100% - 180px)';
                
                if (inputArea) inputArea.style.right = '0';
            }
            
            if (window.innerWidth <= 480) {
                if (header) header.style.left = '140px';
                if (header) header.style.width = 'calc(100% - 140px)';
                if (chatArea) chatArea.style.marginLeft = '140px';
                if (chatArea) chatArea.style.width = 'calc(100% - 140px)';
                
                if (inputArea) inputArea.style.right = '0';
            }
        }
    }

    // Event listeners
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    
    if (hamburgerMenu) {
        hamburgerMenu.addEventListener('click', toggleSidebar);
    }
    
    // Adjust layout on window resize
    window.addEventListener('resize', function() {
        if (!sidebar.classList.contains('collapsed')) {
            // Only adjust if sidebar is visible
            if (window.innerWidth <= 480) {
                if (header) header.style.left = '140px';
                if (header) header.style.width = 'calc(100% - 140px)';
                if (chatArea) chatArea.style.marginLeft = '140px';
                if (chatArea) chatArea.style.width = 'calc(100% - 140px)';
                
                if (inputArea) inputArea.style.right = '0';
            } else if (window.innerWidth <= 768) {
                if (header) header.style.left = '180px';
                if (header) header.style.width = 'calc(100% - 180px)';
                if (chatArea) chatArea.style.marginLeft = '180px';
                if (chatArea) chatArea.style.width = 'calc(100% - 180px)';
                
                if (inputArea) inputArea.style.right = '0';
            } else {
                if (header) header.style.left = '250px';
                if (header) header.style.width = 'calc(100% - 250px)';
                if (chatArea) chatArea.style.marginLeft = '250px';
                if (chatArea) chatArea.style.width = 'calc(100% - 250px)';
                if (inputArea) inputArea.style.marginLeft = '250px';
                if (inputArea) inputArea.style.width = 'calc(100% - 250px)';
            }
        }
    });
});