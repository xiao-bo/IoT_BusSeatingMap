$(function () {

    getdata();

    function getdata() {
        $.post("http://localhost:3000/getdata", function (data) {
            //console.log(data["number"]);
            //console.log(data["seattable"]);

            // animate the number
            c2.innerHTML = data["number"];

            // check the seat is been seated
            for (var i = 1; i <= 8; i++) {
                if (data["seattable"][i - 1] == 1) {
                    $("#s" + i).css("background-image", "url(s2.png)");
                } 
                else {
                    $("#s" + i).css("background-image", "url(s1.png)");
                }
            }
        });

        setTimeout(function () {
            getdata();
        }, 100);
    }
});