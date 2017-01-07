var express = require('express');
var router = express.Router();

router.get('/', function(req, res, next) {
	res.render('seat', { data: 'get'});
	console.log("get");
});

router.post('/', function(req, res, next) {
	res.render('seat', { data: 'post'});
	console.log(req.body.key1[2]);
	console.log("post");
});

/*
// GET home page.
router.get('/', function(req, res, next) {
	res.render('index', { title: 'Express', data: req});
	console.log("good");
});
*/

module.exports = router;
