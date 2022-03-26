$(document).ready(function(){
    $(".subscribe").click(function(){
        console.log("Posting")
        $.ajax({
            type: "POST",
            url: "https://api.blog.claytondavis.dev/prod/api/email/subscribe",
            data: $("#email_input").val(),
            dataType: 'text',
            success: function() {
                console.log("Done")    
                // alert("You have been subscribed");
                $(".popup-overlay, .popup-content").addClass("active");
                $("#email_input").val("")
            },
            error: function() {
                console.log("ERROR")
            }
        });
    });

    $(".close, .popup-overlay").on("click", function() {
        $(".popup-overlay, .popup-content").removeClass("active");
    });

    if (window.location.pathname == "/unsubscribe/" || window.location.pathname == "/unsubscribe/index.html") {
		if (window.location.href.indexOf("?") > -1 && window.location.href.indexOf("email") > -1) {
            var email = window.location.href.split("?")[1].split("=")[1]
            
            $.ajax({
                type: "DELETE",
                url: "https://api.blog.claytondavis.dev/prod/api/email/unsubscribe",
                data: email,
                dataType: 'text',
                success: function() {
                    console.log("Done")    
                    // alert("You have been subscribed");
                    $(".markdown p").text("Unsubscribed "+email+".")
                },
                error: function() {
                    console.log("ERROR")
                    $(".markdown p").text("Error unsubscribing "+email+". Please try agian later, or email blog@claytondavis.dev")
                }
            });
        } else {
            $(".markdown p").text("No email found to unsubscribe")
        }
    }
})

