// console.log("working fine")

const monthNames = ["Jan", "Feb", "Mar", "April", "May", "June",
    "July", "Aug", "Sept", "Oct", "Nov", "Dec"
];

$("#commentForm").submit(function (e) {
    e.preventDefault();
    console.log("Form submission started");
    
    let dt = new Date();
    let monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"];
    let time = dt.getDate() + " " + monthNames[dt.getMonth()] + ", " + dt.getFullYear();
    
    // Show loading state
    const submitBtn = $(this).find('button[type="submit"]');
    const originalText = submitBtn.text();
    submitBtn.prop('disabled', true).text('Submitting...');
    
    // Clear previous messages
    $("#review-res").html('').removeClass('text-success text-danger');
    
    console.log("Sending AJAX request...");
    
    $.ajax({
        data: $(this).serialize(),
        method: $(this).attr("method"),
        url: $(this).attr("action"),
        dataType: "json",
        success: function (res, status, xhr) {
            console.log("AJAX success response:", res);
            console.log("Status:", status);
            
            if (res.bool == true) {
                $("#review-res").html(res.message || "Review added successfully.")
                    .removeClass('text-danger')
                    .addClass('text-success');
                
                $(".hide-comment-form").hide();
                $(".add-review").hide();

                // Create new review HTML
                let _html = '<div class="single-comment justify-content-between d-flex mb-30">';
                _html += '<div class="user justify-content-between d-flex">';
                _html += '<div class="thumb text-center">';
                _html += '<img src="https://thumbs.dreamstime.com/b/default-avatar-profile-vector-user-profile-default-avatar-profile-vector-user-profile-profile-179376714.jpg" alt="" />';
                _html += '<p class="font-heading text-brand">' + res.context.user + '</p>';
                _html += '</div>';
                _html += '<div class="desc">';
                _html += '<div class="d-flex justify-content-between mb-10">';
                _html += '<div class="d-flex align-items-center">';
                _html += '<span class="font-xs text-muted">' + (res.context.date || time) + ' </span>';
                _html += '</div>';
                _html += '<div>';
                
                for (var i = 1; i <= res.context.rating; i++) {
                    _html += '<i class="fas fa-star text-warning"></i>';
                }
                
                _html += '</div>';
                _html += '</div>';
                _html += '<p class="mb-10">' + res.context.review + '</p>';
                _html += '</div>';
                _html += '</div>';
                _html += '</div>';
                
                $(".comment-list").prepend(_html);
                
                // Update average rating display if it exists
                if (res.average_reviews) {
                    $(".average-rating").text(res.average_reviews.toFixed(1));
                }
                
            } else {
                // Show error message
                console.log("Error from server:", res.error);
                $("#review-res").html(res.error || "Error submitting review.")
                    .removeClass('text-success')
                    .addClass('text-danger');
            }
        },
        error: function(xhr, status, error) {
            console.error("AJAX error details:");
            console.error("Status:", status);
            console.error("Error:", error);
            console.error("XHR response:", xhr.responseText);
            console.error("XHR status:", xhr.status);
            
            let errorMsg = "Error submitting review. Please try again.";
            
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                // Couldn't parse JSON response
            }
            
            $("#review-res").html(errorMsg)
                .removeClass('text-success')
                .addClass('text-danger');
        },
        complete: function() {
            console.log("AJAX request complete");
            // Reset button state
            submitBtn.prop('disabled', false).text(originalText);
        }
    });
});


$(document).ready(function () {
    // ========== FILTER FUNCTIONALITY ==========
    $(".filter-checkbox, #price-filter-btn").on("click", function () {
        console.log("A checkbox have been clicked");

        let filter_object = {}
        let min_price = $("#max_price").attr("min")
        let max_price = $("#max_price").val()

        filter_object.min_price = min_price;
        filter_object.max_price = max_price;

        $(".filter-checkbox").each(function () {
            let filter_value = $(this).val()
            let filter_key = $(this).data("filter") // vendor, category

            console.log("Filter value is:", filter_value);
            console.log("Filter key is:", filter_key);

            filter_object[filter_key] = Array.from(document.querySelectorAll('input[data-filter=' + filter_key + ']:checked')).map(function (element) {
                return element.value
            })
        })
        
        console.log("Filter Object is: ", filter_object);
        
        $.ajax({
            url: '/filter-products',
            data: filter_object,
            dataType: 'json',
            beforeSend: function () {
                console.log("Trying to filter product...");
                // Optional: Show loading spinner
                $("#filtered-product").html('<div class="text-center"><i class="fi-rs-spinner fa-spin fa-2x"></i></div>');
            },
            success: function (response) {
                console.log("Data filtered successfully...");
                $(".totall-product").hide()
                $("#filtered-product").html(response.data)
                
                // Update product count
                let productCount = $(response.data).find('.product-cart-wrap').length;
                $(".totall-product p").html(`We found <strong class="text-brand">${productCount}</strong> items for you!`);
                
                console.log(`Loaded ${productCount} products`);
            },
            error: function (xhr, status, error) {
                console.error("Filter error:", error);
                $("#filtered-product").html('<div class="col-12 text-center text-danger">Error loading products. Please try again.</div>');
            }
        })
    });

    
    
    
    // Initialize any other functionality on page load
    console.log("Product filters and event delegation initialized");
    
    // Optional: Add to cart for modal (if you have add-to-cart in modal)
    $(document).on("click", "#quickViewModal .add-to-cart-btn", function() {
        let productId = $(this).attr('data-index');
        let quantity = $("#quickViewModal .product-quantity").val() || 1;
        
        // Get data from modal inputs
        let product_title = $("#quickViewModal .product-title-input").val();
        let product_price = $("#quickViewModal .product-price-input").val();
        let product_pid = $("#quickViewModal .product-pid").val();
        let product_image = $("#quickViewModal .product-image-input").val();
        let product_sku = $("#quickViewModal .product-sku-input").val();
        
        console.log("Adding from modal:", productId, product_title);
        
        // Reuse the same AJAX call
        $.ajax({
            url: '/add-to-cart',
            data: {
                'id': productId,
                'pid': product_pid,
                'image': product_image,
                'qty': quantity,
                'title': product_title,
                'price': product_price,
                'sku': product_sku
            },
            dataType: 'json',
            beforeSend: function () {
                console.log("Adding Product to Cart from modal...");
            },
            success: function (response) {
                console.log("Added Product to Cart from modal!");
                $(".cart-items-count").text(response.totalcartitems);
                $('#quickViewModal').modal('hide');
                showNotification('Product added to cart successfully!', 'success');
            }
        });
    });

    
    // Add to cart functionality

// Notification function
function showNotification(type, message) {
    // Remove any existing notifications
    $('.cart-notification').remove();
    
    // Create notification
    let notification = $('<div class="cart-notification"></div>');
    notification.css({
        'position': 'fixed',
        'top': '20px',
        'right': '20px',
        'padding': '15px 20px',
        'border-radius': '8px',
        'color': 'white',
        'font-weight': '600',
        'z-index': '9999',
        'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
        'animation': 'slideIn 0.3s ease'
    });
    
    if (type === 'success') {
        notification.css('background-color', '#3BB77E');
    } else {
        notification.css('background-color', '#ff6b6b');
    }
    
    notification.html(`
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
        ${message}
    `);
    
    $('body').append(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.animate({opacity: 0, right: '-100px'}, 300, function() {
            $(this).remove();
        });
    }, 3000);
}

// Add CSS for animation
$('head').append(`
<style>
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(100px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
</style>
`);
    // delete from cart functionality
    $(document).on("click", ".delete-product", function () {
        let product_key = $(this).attr("data-product")  // This is now the unique key
        let this_val = $(this)
    
        console.log("Product Key:", product_key);
    
        $.ajax({
            url: "/delete-from-cart",
            data: {
                "id": product_key  // Send the unique key
            },
            dataType: "json",
            beforeSend: function () {
                this_val.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');
            },
            success: function (response) {
                this_val.prop('disabled', false).html('<i class="fi-rs-trash"></i>');
                $(".cart-items-count").text(response.totalcartitems);
                $("#cart-list").html(response.data);
                window.location.reload()
                showNotification('success', 'Item removed from cart');
            },
            error: function() {
                this_val.prop('disabled', false).html('<i class="fi-rs-trash"></i>');
                showNotification('error', 'Error removing item');
            }
        })
    });
    
    // Update cart functionality
    $(document).on("click", ".update-product", function () {
        let product_key = $(this).attr("data-product")  // This is now the unique key
        let this_val = $(this)
        let product_quantity = $(".product-qty-" + product_key).val()
    
        console.log("Product Key:", product_key);
        console.log("Product QTY:", product_quantity);
    
        $.ajax({
            url: "/update-cart",
            data: {
                "id": product_key,  // Send the unique key
                "qty": product_quantity,
            },
            dataType: "json",
            beforeSend: function () {
                this_val.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');
            },
            success: function (response) {
                this_val.prop('disabled', false).html('<i class="fi-rs-refresh"></i>');
                $(".cart-items-count").text(response.totalcartitems);
                $("#cart-list").html(response.data);
                window.location.reload()
                showNotification('success', 'Cart updated successfully');
            },
            error: function() {
                this_val.prop('disabled', false).html('<i class="fi-rs-refresh"></i>');
                showNotification('error', 'Error updating cart');
            }
        })
    });


    // Making Default Address
    $(document).on("click", ".make-default-address", function () {
        let id = $(this).attr("data-address-id")
        let this_val = $(this)

        // console.log("ID is:", id);
        // console.log("Element is:", this_val);

        $.ajax({
            url: "/make-default-address",
            data: {
                "id": id
            },
            dataType: "json",
            success: function (response) {
                console.log("Address Made Default....");
                if (response.boolean == true) {

                    $(".check").hide()
                    $(".action_btn").show()

                    $(".check" + id).show()
                    $(".button" + id).hide()

                }
            }
        })
    });



    // add to Wishlist Functionality
    $(document).on("click", ".add-to-wishlist", function () {
        let product_id = $(this).attr("data-product-item")
        let this_val = $(this)


        // console.log("PRoduct ID is", product_id);
        $.ajax({
            url: "/add-to-wishlist",
            data: {
                "id": product_id
            },
            dataType: "json",
            beforeSend: function () {
                console.log("Adding to wishlist...")
            },
            success: function (response) {
                // this_val.html("✓")
                this_val.html("<i class='fas fa-heart text-danger'></i>")
                if (response.bool === true) {
                    console.log("Added to wishlist...");
                }
            }
        })




    });
    // remove from Wishlist Functionality
    $(document).on("click", ".delete-wishlist-product", function () {
        let wishlist_id = $(this).attr("data-wishlist-product")
        let this_val = $(this)

        // console.log("wishlist id is:", wishlist_id);

        $.ajax({
            url: "/remove-from-wishlist",
            data: {
                "id": wishlist_id
            },
            dataType: "json",
            beforeSend: function () {
                console.log("Deleting product from wishlist...");
            },
            success: function (response) {
                $("#wishlist-list").html(response.data)
                console.log("Deleted from wishlist...");
            }
        })
    });



    // contact useCallback(
        $(document).on("submit", "#contact-form-ajax", function (e) {
            e.preventDefault()
            console.log("Submited...");
    
            let full_name = $("#full_name").val()
            let email = $("#email").val()
            let phone = $("#phone").val()
            let subject = $("#subject").val()
            let message = $("#message").val()
    
            // console.log("Name:", full_name);
            // console.log("Email:", email);
            // console.log("Phone:", phone);
            // console.log("Subject:", subject);
            // console.log("MEssage:", message);
    
            $.ajax({
                url: "/ajax-contact-form",
                data: {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "subject": subject,
                    "message": message,
                },
                dataType: "json",
                beforeSend: function () {
                    // console.log("Sending Data to Server...");
                },
                success: function (res) {
                    // console.log("Sent Data to server!");
                    $(".contact_us_p").hide()
                    $("#contact-form-ajax").hide()
                    $("#message-response").html("Message sent successfully, we will get back to you soon.")
                }
            })
        })
    

});



$("#max_price").on("blur", function () {
    let min_price = $(this).attr("min")
    let max_price = $(this).attr("max")
    let current_price = $(this).val()

    // console.log("Current Price is:", current_price);
    // console.log("Max Price is:", max_price);
    // console.log("Min Price is:", min_price);

    if (current_price < parseInt(min_price) || current_price > parseInt(max_price)) {
        // console.log("Price Error Occured");

        min_price = Math.round(min_price * 100) / 100
        max_price = Math.round(max_price * 100) / 100


        // console.log("Max Price is:", min_Price);
        // console.log("Min Price is:", max_Price);

        alert("Price must between Ksh " + min_price + ' and Ksh ' + max_price)
        $(this).val(min_price)
        $('#range').val(min_price)

        $(this).focus()

        return false

    }

});

