console.log("working fine")

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
        console.log("Filter Object is: ", filter_object);
        $.ajax({
            url: '/filter-products',
            data: filter_object,
            dataType: 'json',
            beforeSend: function () {
                console.log("Trying to filter product...");
            },
            success: function (response) {
                console.log(response.length);
                console.log("Data filtred successfully...");
                $(".totall-product").hide()
                $("#filtered-product").html(response.data)
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


// Add to cart functionality
    $(".add-to-cart-btn").on("click", function () {
        let this_val = $(this)
        let quantity = $("#product-quantity").val()
        let product_title = $("#product-title").val()

        let product_id = $(".product-id").val()
        let product_price = $("#current-product-price").text()

        console.log("Quantity:", quantity);
        console.log("Title:", product_title);
        console.log("Price:", product_price);
        console.log("ID:", product_id);
        console.log("Currrent Element:", this_val);

        $.ajax({
            url: '/add-to-cart',
            data: {
                'id': product_id,
                'qty': quantity,
                'title': product_title,
                'price': product_price,
            },
            dataType: 'json',
            beforeSend: function () {
                console.log("Adding Product to Cart...");
            },
            success: function (response) {
                // this_val.html("Item added to cart")
                this_val.html("<i class='fas fa-check-circle'></i>")

                console.log("Added Product to Cart!");
                $(".cart-items-count").text(response.totalcartitems)


            }
        })


    });
