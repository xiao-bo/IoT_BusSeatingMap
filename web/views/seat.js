$(function () {

    /*
    setTimeout(function () {
        c2.innerHTML = 21;
	}, 100);
	*/
    getdata();
    function getdata() {
        $.post("http://localhost:3000/getdata", function (data) {
            console.log(data);
            console.log(data["number"]);
            console.log(data["seattable"][0]);
            c2.innerHTML = data["number"];
        });

        setTimeout(function () {
            getdata();
        }, 1000);
    }
});