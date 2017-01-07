var express = require('express');
var router = express.Router();

var number = 0;
var seattable = [0, 0, 0, 0, 0, 0, 0, 0];

router.get('/', function(req, res, next) {
	res.render('seat', {number: number});
	console.log("get");
});

router.post('/', function(req, res, next) {
	res.json({data: "good"});
	seattable = req.body.seat;
	console.log(seattable);
	number = number + 1;
	console.log("post");
});

router.post('/getdata', function(req, res, next) {
	res.json({number: number, seattable: seattable});
	console.log("getdata");
});

module.exports = router;
