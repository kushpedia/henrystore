// console.log("working fine")

const monthNames = ["Jan", "Feb", "Mar", "April", "May", "June",
    "July", "Aug", "Sept", "Oct", "Nov", "Dec"
];


$("#commentForm").submit(function (e) {
    e.preventDefault();
	let dt = new Date();
    let time = dt.getDay() + " " + monthNames[dt.getUTCMonth()] + ", " + dt.getFullYear()
	$.ajax({
        data: $(this).serialize(),
		method: $(this).attr("method"),

        url: $(this).attr("action"),

        dataType: "json",
		success: function (res) {
            console.log("Comment Saved to DB...");

            if (res.bool == true) {
                $("#review-res").html("Review added successfully.")
                $(".hide-comment-form").hide()
                $(".add-review").hide()

                let _html = '<div class="single-comment justify-content-between d-flex mb-30">'
                _html += '<div class="user justify-content-between d-flex">'
                _html += '<div class="thumb text-center">'
                _html += '<img src="https://thumbs.dreamstime.com/b/default-avatar-profile-vector-user-profile-default-avatar-profile-vector-user-profile-profile-179376714.jpg" alt="" />'
                _html += '<a href="#" class="font-heading text-brand">' + res.context.user + '</a>'
                _html += '</div>'

                _html += '<div class="desc">'
                _html += '<div class="d-flex justify-content-between mb-10">'
                _html += '<div class="d-flex align-items-center">'
                _html += '<span class="font-xs text-muted">' + time + ' </span>'
                _html += '</div>'

                for (var i = 1; i <= res.context.rating; i++) {
                    _html += '<i class="fas fa-star text-warning"></i>';
                }


                _html += '</div>'
                _html += '<p class="mb-10">' + res.context.review + '</p>'

                _html += '</div>'
                _html += '</div>'
                _html += ' </div>'
				
                $(".comment-list").prepend(_html)
            }


        }
    })
})



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

    // ========== EVENT DELEGATION FOR DYNAMICALLY LOADED CONTENT ==========
    
    // Add to Cart button - USING EVENT DELEGATION
    $(document).on("click", ".add-to-cart-btn", function () {
        console.log("Add to cart button clicked");

        let this_val = $(this);
        let index = this_val.attr("data-index");

        let quantity = $(".product-quantity-" + index).val();
        let product_title = $(".product-title-" + index).val();
        let product_sku = $(".product-sku-" + index).val();
        let product_id = $(".product-id-" + index).val();
        let product_price = $(".current-product-price-" + index).text();
        let product_pid = $(".product-pid-" + index).val();
        let product_image = $(".product-image-" + index).val();

        console.log("Quantity:", quantity);
        console.log("Title:", product_title);
        console.log("Price:", product_price);
        console.log("ID:", product_id);
        console.log("PID:", product_pid);
        console.log("Image:", product_image);
        console.log("Index:", index);
        console.log("Current Element:", this_val);

        $.ajax({
            url: '/add-to-cart',
            data: {
                'id': product_id,
                'pid': product_pid,
                'image': product_image,
                'qty': quantity,
                'title': product_title,
                'price': product_price,
                'sku': product_sku
            },
            dataType: 'json',
            beforeSend: function () {
                console.log("Adding Product to Cart...");
                // Optional: Show loading state
                this_val.prop('disabled', true);
                this_val.html('<i class="fi-rs-spinner fa-spin mr-5"></i>Adding...');
            },
            success: function (response) {
                console.log("Added Product to Cart!");
                
                // Update button appearance
                this_val.html('<i class="fas fa-check-circle mr-5"></i>Added');
                this_val.removeClass('btn-primary').addClass('btn-success');
                
                // Update cart count
                $(".cart-items-count").text(response.totalcartitems);
                                
                // Reset button after 2 seconds
                setTimeout(function() {
                    this_val.html('<i class="fi-rs-shopping-cart mr-5"></i>Add');
                    this_val.removeClass('btn-success').addClass('btn-primary');
                    this_val.prop('disabled', false);
                }, 5000);
            },
            error: function (xhr, status, error) {
                console.error("Error adding to cart:", error);
                this_val.html('<i class="fi-rs-shopping-cart mr-5"></i>Add');
                this_val.prop('disabled', false);
                showNotification('Failed to add product to cart', 'error');
            }
        });
    });

    // Quick View button - USING EVENT DELEGATION
    $(document).on("click", ".quick-view-btn", function(e) {
        e.preventDefault();
        
        console.log("Quick view clicked");
        
        // Get data attributes
        let productId = $(this).data("id");
        let title = $(this).data("title");
        let price = $(this).data("price");
        let oldPrice = $(this).data("oldprice");
        let image = $(this).data("image");
        let description = $(this).data("description");
        let vendor = $(this).data("vendor");
        let percentage = $(this).data("percentage");
        let pid = $(this).data("pid");
        
        console.log("Quick view for product:", title);
        
        // Populate modal with data
        $('#quickViewModal .product-title').text(title);
        $('#quickViewModal .product-price').text('Ksh ' + price);
        if (oldPrice) {
            $('#quickViewModal .product-old-price').text('Ksh ' + oldPrice).show();
        } else {
            $('#quickViewModal .product-old-price').hide();
        }
        $('#quickViewModal .product-image').attr('src', image);
        $('#quickViewModal .product-description').text(description);
        $('#quickViewModal .product-vendor').text(vendor);
        if (percentage) {
            $('#quickViewModal .product-percentage').text(percentage + '% OFF').show();
        } else {
            $('#quickViewModal .product-percentage').hide();
        }
        
        // Update hidden fields in modal for add-to-cart
        $('#quickViewModal .product-pid').val(pid);
        $('#quickViewModal .product-id').val(productId);
        $('#quickViewModal .product-title-input').val(title);
        $('#quickViewModal .product-price-input').val(price);
        $('#quickViewModal .product-image-input').val(image);
        $('#quickViewModal .product-sku-input').val($(this).data("sku") || "");
        
        // Update add to cart button in modal
        $('#quickViewModal .add-to-cart-btn').attr('data-index', productId);
        
        // Show modal
        $('#quickViewModal').modal('show');
    });

    // Add to Wishlist button - USING EVENT DELEGATION
    $(document).on("click", ".add-to-wishlist", function(e) {
        e.preventDefault();
        
        let productId = $(this).data("product-item");
        console.log("Add to wishlist clicked for product ID:", productId);
        
        // Get product data from hidden inputs
        let title = $(".product-title-" + productId).val();
        let price = $(".current-product-price-" + productId).text().trim();
        let image = $(".product-image-" + productId).val();
        let sku = $(".product-sku-" + productId).val();
        let pid = $(".product-pid-" + productId).val();
        
        console.log("Adding to wishlist:", {
            id: productId,
            title: title,
            price: price
        });

        let this_val = $(this);
        let icon = this_val.find('i');
        
        $.ajax({
            url: '/add-to-wishlist', // Update with your actual URL
            data: {
                'id': productId,
                'title': title,
                'price': price,
                'image': image,
                'sku': sku,
                'pid': pid
            },
            dataType: 'json',
            beforeSend: function () {
                console.log("Adding to wishlist...");
                icon.css('fill', '#ff6b6b'); // Change to red while loading
            },
            success: function (response) {
                console.log("Added to wishlist!");
                icon.css('fill', 'red'); // Keep red on success
                
                // Optional: Update wishlist count if you have one
                if (response.totalwishlistitems) {
                    $(".wishlist-items-count").text(response.totalwishlistitems);
                }
                
                showNotification('Added to wishlist!', 'success');
            },
            error: function (xhr, status, error) {
                console.error("Error adding to wishlist:", error);
                icon.css('fill', ''); // Reset color
                showNotification('Failed to add to wishlist', 'error');
            }
        });
    });

    // Price range slider update - USING EVENT DELEGATION
    $(document).on("input change", "#range, #max_price", function() {
        let rangeValue = $("#range").val();
        let maxPriceValue = $("#max_price").val();
        
        // Keep them in sync
        if($(this).attr("id") === "range") {
            $("#max_price").val(rangeValue);
        } else {
            $("#range").val(maxPriceValue);
        }
        
        // Update display
        $("#slider-range-value2").text("Ksh " + maxPriceValue);
    });

    // ========== HELPER FUNCTIONS ==========
    
    // Show notification
    function showNotification(message, type = 'success') {
        // You can use a toast notification library or implement your own
        // For now, using alert as fallback
        console.log(`${type.toUpperCase()}: ${message}`);
        
    }
    
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
    $(".add-to-cart-btn").on("click", function () {
        console.log("Add to cart button clicked");

        let this_val = $(this)
        let index = this_val.attr("data-index")

        let quantity = $(".product-quantity-" + index).val()
        let product_title = $(".product-title-" + index).val()
        let product_sku = $(".product-sku-" + index).val()

        let product_id = $(".product-id-" + index).val()
        let product_price = $(".current-product-price-" + index).text()

        let product_pid = $(".product-pid-" + index).val()
        let product_image = $(".product-image-" + index).val()


        console.log("Quantity:", quantity);
        console.log("Title:", product_title);
        console.log("Price:", product_price);
        console.log("ID:", product_id);
        console.log("PID:", product_pid);
        console.log("Image:", product_image);
        console.log("Index:", index);
        console.log("Currrent Element:", this_val);

        $.ajax({
            url: '/add-to-cart',
            data: {
                'id': product_id,
                'pid': product_pid,
                'image': product_image,
                'qty': quantity,
                'title': product_title,
                'price': product_price,
                'sku':product_sku
            },
            dataType: 'json',
            beforeSend: function () {
                console.log("Adding Product to Cart...");
            },
            success: function (response) {
                // this_val.html("✓")
                this_val.html("<i class='fas fa-check-circle'></i>")

                console.log("Added Product to Cart!");
                $(".cart-items-count").text(response.totalcartitems)


            }
        })
    });
    // delete from cart functionality
    $(document).on("click", ".delete-product", function () {

        let product_id = $(this).attr("data-product")
        let this_val = $(this)

        console.log("Product ID:", product_id);

        $.ajax({
            url: "/delete-from-cart",
            data: {
                "id": product_id
            },
            dataType: "json",
            beforeSend: function () {
                this_val.hide()
            },
            success: function (response) {
                this_val.show()
                $(".cart-items-count").text(response.totalcartitems)
                $("#cart-list").html(response.data)
                window.location.reload()
            }
        })

    });

    // update cart functionality
    $(".update-product").on("click", function () {

        let product_id = $(this).attr("data-product")
        let this_val = $(this)
        let product_quantity = $(".product-qty-" + product_id).val()

        console.log("PRoduct ID:", product_id);
        console.log("PRoduct QTY:", product_quantity);

        $.ajax({
            url: "/update-cart",
            data: {
                "id": product_id,
                "qty": product_quantity,
            },
            dataType: "json",
            beforeSend: function () {
                this_val.hide()
            },
            success: function (response) {
                this_val.show()
                $(".cart-items-count").text(response.totalcartitems)
                $("#cart-list").html(response.data)
                window.location.reload()

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
                    console.log("Sending Data to Server...");
                },
                success: function (res) {
                    console.log("Sent Data to server!");
                    $(".contact_us_p").hide()
                    $("#contact-form-ajax").hide()
                    $("#message-response").html("Message sent successfully.")
                }
            })
        })
    

});



$("#max_price").on("blur", function () {
    let min_price = $(this).attr("min")
    let max_price = $(this).attr("max")
    let current_price = $(this).val()

    console.log("Current Price is:", current_price);
    console.log("Max Price is:", max_price);
    console.log("Min Price is:", min_price);

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

