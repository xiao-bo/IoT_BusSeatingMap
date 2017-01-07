var express = require('express');
var router = express.Router();

var number = 0;
var seattable = [0, 0, 0, 0, 0, 0, 0, 0];

router.get('/', function(req, res, next) {
	res.render('seat', {number: number});
	console.log("get");
});

router.post('/thermal', function(req, res, next) {
	res.json({data: "good"});
	seattable = req.body.seat;
	console.log(seattable);
	console.log("post: seattable");
});

router.post('/ir', function(req, res, next) {
	res.json({data: "good"});
	number = req.body.count;
	console.log(number);
	console.log("post: number");
});
router.post('/getdata', function(req, res, next) {
	res.json({number: number, seattable: seattable});
	console.log("getdata");
});

module.exports = router;
