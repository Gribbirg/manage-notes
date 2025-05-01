/**
 * Tags functionality for Notes Manager
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle tag input
    const tagInput = document.getElementById('id_new_tags');
    if (!tagInput) return;
    
    // Current tags for autocomplete
    let availableTags = [];
    
    // Get existing tags from select field
    const tagSelect = document.getElementById('id_tags');
    if (tagSelect) {
        for (let option of tagSelect.options) {
            availableTags.push(option.text.trim());
        }
    }
    
    // Split tags on comma
    tagInput.addEventListener('keyup', function(e) {
        if (e.key === ',') {
            const value = this.value;
            const lastCommaIndex = value.lastIndexOf(',');
            
            if (lastCommaIndex !== -1) {
                const tagName = value.substring(0, lastCommaIndex).trim();
                if (tagName) {
                    // Focus input again after inserting comma
                    this.focus();
                }
            }
        }
    });
    
    // Show autocomplete suggestions
    tagInput.addEventListener('input', function() {
        removeAutocomplete();
        
        const value = this.value;
        const lastCommaIndex = value.lastIndexOf(',');
        const currentTag = lastCommaIndex !== -1 ? value.substring(lastCommaIndex + 1).trim() : value.trim();
        
        if (currentTag.length < 2) return;
        
        // Get matching tags
        const matchingTags = availableTags.filter(tag => 
            tag.toLowerCase().includes(currentTag.toLowerCase()) && 
            !getEnteredTags().includes(tag.toLowerCase())
        );
        
        if (matchingTags.length === 0) return;
        
        // Create autocomplete container
        const autocompleteContainer = document.createElement('div');
        autocompleteContainer.id = 'tag-autocomplete';
        autocompleteContainer.className = 'tag-autocomplete';
        
        // Position below the input
        const rect = this.getBoundingClientRect();
        autocompleteContainer.style.position = 'absolute';
        autocompleteContainer.style.left = rect.left + 'px';
        autocompleteContainer.style.top = (rect.bottom + window.scrollY) + 'px';
        autocompleteContainer.style.width = rect.width + 'px';
        autocompleteContainer.style.maxHeight = '150px';
        autocompleteContainer.style.overflowY = 'auto';
        autocompleteContainer.style.backgroundColor = '#fff';
        autocompleteContainer.style.border = '1px solid #ced4da';
        autocompleteContainer.style.borderRadius = '0.25rem';
        autocompleteContainer.style.zIndex = '1000';
        
        // Add matching tags to the container
        matchingTags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag-autocomplete-item';
            tagElement.textContent = tag;
            tagElement.style.padding = '5px 10px';
            tagElement.style.cursor = 'pointer';
            
            // Hover effect
            tagElement.addEventListener('mouseover', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            tagElement.addEventListener('mouseout', function() {
                this.style.backgroundColor = '#fff';
            });
            
            // Select tag on click
            tagElement.addEventListener('click', function() {
                const tagName = this.textContent.trim();
                const inputValue = tagInput.value;
                
                if (lastCommaIndex !== -1) {
                    // Replace the current tag
                    tagInput.value = inputValue.substring(0, lastCommaIndex + 1) + ' ' + tagName + ', ';
                } else {
                    // First tag
                    tagInput.value = tagName + ', ';
                }
                
                removeAutocomplete();
                tagInput.focus();
            });
            
            autocompleteContainer.appendChild(tagElement);
        });
        
        document.body.appendChild(autocompleteContainer);
    });
    
    // Remove autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== tagInput) {
            removeAutocomplete();
        }
    });
    
    // Helper to remove autocomplete
    function removeAutocomplete() {
        const existingAutocomplete = document.getElementById('tag-autocomplete');
        if (existingAutocomplete) {
            existingAutocomplete.parentNode.removeChild(existingAutocomplete);
        }
    }
    
    // Helper to get current entered tags
    function getEnteredTags() {
        const value = tagInput.value;
        if (!value) return [];
        
        return value.split(',')
            .map(tag => tag.trim().toLowerCase())
            .filter(tag => tag.length > 0);
    }
}); 