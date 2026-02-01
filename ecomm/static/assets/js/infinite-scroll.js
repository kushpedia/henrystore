
$(document).ready(function() {
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        initInfiniteScroll();
    }
    
    function initInfiniteScroll() {
        let isLoading = false;
        let nextPage = 2; // Start from page 2 (since page 1 is already loaded)
        let hasNextPage = true;
        
        // Load More Button Click
        $(document).on('click', '#load-more-btn', function(e) {
            e.preventDefault();
            if (!isLoading && hasNextPage) {
                loadMoreProducts();
            }
        });
        
        // Infinite Scroll
        let scrollTimer;
        $(window).on('scroll', function() {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(function() {
                if (!isLoading && hasNextPage && isAtBottom()) {
                    loadMoreProducts();
                }
            }, 200);
        });
        
        
        
        function loadMoreProducts() {
            if (isLoading || !hasNextPage) return;
            
            isLoading = true;
            
            // Show loader
            $('#infinite-scroll-loader').fadeIn(300);
            $('#load-more-btn').prop('disabled', true).html('<i class="fi-rs-refresh mr-2"></i> Loading...');
            
            // Get current URL parameters
            const currentUrl = window.location.pathname;
            const queryParams = new URLSearchParams(window.location.search);
            
            // Update page parameter
            queryParams.set('page', nextPage);
            
            // Build AJAX URL
            const ajaxUrl = `${currentUrl}?${queryParams.toString()}`;
            
            // AJAX request
            $.ajax({
                url: ajaxUrl,
                type: 'GET',
                dataType: 'json',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: function(response) {
                    if (response.products_html) {
                        // Append new products with fade-in animation
                        const $newProducts = $(response.products_html);
                        $newProducts.hide();
                        $('.product-grid').append($newProducts);
                        $newProducts.fadeIn(500);
                        
                        // Update next page
                        if (response.has_next) {
                            nextPage = response.next_page_number;
                            hasNextPage = true;
                            
                            // Update button
                            $('#load-more-btn').prop('disabled', false).html('<i class="fi-rs-refresh mr-2"></i> Load More Products');
                            
                            // Show success message
                            showNotification('New products loaded!', 'success');
                        } else {
                            // No more pages
                            hasNextPage = false;
                            $('#load-more-btn').hide();
                            $('#infinite-scroll-loader').hide();
                            $('.end-of-content').show();
                        }
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error loading more products:', xhr.responseText || error);
                    showNotification('Failed to load more products. Please try again.', 'error');
                    
                    // Re-enable button on error
                    $('#load-more-btn').prop('disabled', false).html('<i class="fi-rs-refresh mr-2"></i> Load More Products');
                },
                complete: function() {
                    isLoading = false;
                    $('#infinite-scroll-loader').fadeOut(300);
                }
            });
        }
        
        function showNotification(message, type) {
            // Remove existing notifications
            $('.scroll-notification').remove();
            
            const bgColor = type === 'success' ? '#3bb77e' : '#dc3545';
            const icon = type === 'success' ? 'fi-rs-check-circle' : 'fi-rs-exclamation-circle';
            
            const notification = $(`
                <div class="scroll-notification">
                    <i class="${icon} mr-2"></i> ${message}
                </div>
            `);
            
            $('body').append(notification);
            
            // Style the notification
            notification.css({
                position: 'fixed',
                bottom: '20px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: bgColor,
                color: 'white',
                padding: '12px 24px',
                borderRadius: '25px',
                zIndex: '9999',
                boxShadow: '0 5px 15px rgba(0,0,0,0.2)',
                fontSize: '14px',
                fontWeight: '500',
                animation: 'slideUp 0.3s ease, fadeOut 0.3s ease 2s forwards',
                whiteSpace: 'nowrap'
            });
            
            // Add CSS for animation
            if (!$('#notification-styles').length) {
                const styles = `
                    @keyframes slideUp {
                        from { bottom: -50px; opacity: 0; }
                        to { bottom: 20px; opacity: 1; }
                    }
                    @keyframes fadeOut {
                        from { opacity: 1; }
                        to { opacity: 0; }
                    }
                `;
                $('<style id="notification-styles">').text(styles).appendTo('head');
            }
            
            setTimeout(() => notification.remove(), 2500);
        }
    }
    
    // Re-initialize on resize
    $(window).resize(function() {
        const newIsMobile = window.innerWidth <= 768;
        if (newIsMobile !== isMobile) {
            location.reload();
        }
    });
});