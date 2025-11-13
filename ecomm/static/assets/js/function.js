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

            // console.log("Filter value is:", filter_value);
            // console.log("Filter key is:", filter_key);

            filter_object[filter_key] = Array.from(document.querySelectorAll('input[data-filter=' + filter_key + ']:checked')).map(function (element) {
                return element.value
            })
        })
        // console.log("Filter Object is: ", filter_object);
        $.ajax({
            url: '/filter-products',
            data: filter_object,
            dataType: 'json',
            beforeSend: function () {
                console.log("Trying to filter product...");
            },
            success: function (response) {
                // console.log(response.length);
                console.log("Data filtred successfully...");
                $(".totall-product").hide()
                $("#filtered-product").html(response.data)
            }
        })
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
            }
        })

    });

    // update cart functionality
    $(".update-product").on("click", function () {

        let product_id = $(this).attr("data-product")
        let this_val = $(this)
        let product_quantity = $(".product-qty-" + product_id).val()

        // console.log("PRoduct ID:", product_id);
        // console.log("PRoduct QTY:", product_quantity);

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

