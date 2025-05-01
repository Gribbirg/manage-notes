/**
 * Theme toggle functionality for Notes Manager
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Theme script loaded');
    
    // Get the theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) {
        console.error('Theme toggle button not found');
        return;
    }
    
    console.log('Theme toggle button found:', themeToggle);
    
    // Check if user has a saved preference
    const savedTheme = localStorage.getItem('theme');
    console.log('Saved theme:', savedTheme);
    
    // Apply saved theme or default to light
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcon('dark');
        console.log('Applied dark theme');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        updateThemeIcon('light');
        console.log('Applied light theme (default)');
    }
    
    // Toggle theme when the button is clicked
    themeToggle.addEventListener('click', function(e) {
        console.log('Theme toggle clicked');
        e.preventDefault();
        
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        console.log('Switching from', currentTheme, 'to', newTheme);
        
        // Update data attribute
        html.setAttribute('data-theme', newTheme);
        
        // Save preference
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        updateThemeIcon(newTheme);
        
        console.log('Theme switched to:', newTheme);
    });
    
    // Update the theme toggle icon based on current theme
    function updateThemeIcon(theme) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'fas fa-sun'; // Sun icon for dark mode (to switch to light)
            } else {
                icon.className = 'fas fa-moon'; // Moon icon for light mode (to switch to dark)
            }
            console.log('Icon updated to:', icon.className);
        } else {
            console.error('Icon element not found inside theme toggle');
        }
    }
}); 