
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
        
        function isAtBottom() {
            const scrollTop = $(window).scrollTop();
            const windowHeight = $(window).height();
            const documentHeight = $(document).height();
            const distanceFromBottom = 300; // Load when 300px from bottom
            
            return (scrollTop + windowHeight) >= (documentHeight - distanceFromBottom);
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