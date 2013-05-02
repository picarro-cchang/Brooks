
var CT = require('./modules/country-list');
var AM = require('./modules/account-manager');
var EM = require('./modules/email-dispatcher');
var SU = require('./modules/short_url');

module.exports = function(app) {

// main login page //

 app.get('/investigator/login', function(req, res){
	// check if the user's credentials are saved in a cookie //
		if (req.cookies.user == undefined || req.cookies.pass == undefined){
			res.render('login', { title: 'Hello - Please Login To Your Account' });
		}	else{
	// attempt automatic login //
			AM.autoLogin(req.cookies.user, req.cookies.pass, function(o){
				if (o != null){
				    req.session.user = o;
					res.redirect('/investigator/home');
				}	else{
					res.render('login', { title: 'Hello - Please Login To Your Account' });
				}
			});
		}
	});


	app.get('/', function(req, res){
	// check if the user's credentials are saved in a cookie //
		if (req.cookies.user == undefined || req.cookies.pass == undefined){
			res.render('login', { title: 'Hello - Please Login To Your Account' });
		}	else{
	// attempt automatic login //
			AM.autoLogin(req.cookies.user, req.cookies.pass, function(o){
				if (o != null){
				    req.session.user = o;
					res.redirect('/home');
				}	else{
					res.render('login', { title: 'Hello - Please Login To Your Account' });
				}
			});
		}
	});
	
	app.post('/', function(req, res){
		AM.manualLogin(req.param('user'), req.param('pass'), function(e, o){
			if (!o){
				res.send(e, 400);
			}	else{
			    req.session.user = o;
				if (req.param('remember-me') == 'true'){
					res.cookie('user', o.user, { maxAge: 900000 });
					res.cookie('pass', o.pass, { maxAge: 900000 });
				}
				res.send(o, 200);
			}
		});
	});

	app.post('/investigator/login', function(req, res){
		AM.manualLogin(req.param('user'), req.param('pass'), function(e, o){
			if (!o){
				res.send(e, 400);
			}	else{
			    req.session.user = o;
				if (req.param('remember-me') == 'true'){
					res.cookie('user', o.user, { maxAge: 900000 });
					res.cookie('pass', o.pass, { maxAge: 900000 });
				}
				res.send(o, 200);
			}
		});
	});
	
	
// logged-in user homepage //
	
	app.get('/home', function(req, res) {
	    if (req.session.user == null){
	// if user is not logged-in redirect back to login page //
	        res.redirect('/');
	    }   else{
			res.render('home', {
				title : 'Control Panel',
				countries : CT,
				udata : req.session.user
			});
	    }
	});

	app.get('/investigator/home', function(req, res) {
	    if (req.session.user == null){
	// if user is not logged-in redirect back to login page //
	        res.redirect('/');
	    }   else{
			res.render('home', {
				title : 'Control Panel',
				countries : CT,
				udata : req.session.user
			});
	    }
	});


	app.post('/home', function(req, res){
		if (req.param('user') != undefined) {
			console.log(req.param('anz-identity'));
			AM.updateAccount({
				user 		: req.param('email'),
				name 		: req.param('name'),
				email 		: req.param('email'),
				bio 		: req.param('bio'),
				experimentInfo 		: req.param('experimentInfo'),
				country 	: req.param('country'),
				pass		: req.param('pass'),
				anz		: req.param('anz'),
				anzName		: req.param('anz-name'),
				anzIdentity		: req.param('anz-identity')
			}, function(e, o){
				if (e){
					res.send('error-updating-account', 400);
				}	else{
					req.session.user = o;
			    // update the user's login cookies if they exists //
					if (req.cookies.user != undefined && req.cookies.pass != undefined){
						res.cookie('user', o.user, { maxAge: 900000 });
						res.cookie('pass', o.pass, { maxAge: 900000 });	
					}
					res.send('ok', 200);
				}
			});
		}	else if (req.param('logout') == 'true'){
			res.clearCookie('user');
			res.clearCookie('pass');
			req.session.destroy(function(e){ res.send('ok', 200); });
		}
	});
	
		app.post('/investigator/home', function(req, res){
		if (req.param('user') != undefined) {
			console.log(req.param('anz-identity'));
			AM.updateAccount({
				user 		: req.param('email'),
				name 		: req.param('name'),
				email 		: req.param('email'),
				bio 		: req.param('bio'),
				experimentInfo 		: req.param('experimentInfo'),
				country 	: req.param('country'),
				pass		: req.param('pass'),
				anz		: req.param('anz'),
				anzName		: req.param('anz-name'),
				anzIdentity		: req.param('anz-identity')
			}, function(e, o){
				if (e){
					res.send('error-updating-account', 400);
				}	else{
					req.session.user = o;
			    // update the user's login cookies if they exists //
					if (req.cookies.user != undefined && req.cookies.pass != undefined){
						res.cookie('user', o.user, { maxAge: 900000 });
						res.cookie('pass', o.pass, { maxAge: 900000 });	
					}
					res.send('ok', 200);
				}
			});
		}	else if (req.param('logout') == 'true'){
			res.clearCookie('user');
			res.clearCookie('pass');
			req.session.destroy(function(e){ res.send('ok', 200); });
		}
	});
	

// logged-in user profile //
	
	app.get('/profile', function(req, res) {
	    if (req.session.user == null){
	// if user is not logged-in redirect back to login page //
	        res.redirect('/');
	    }   else{
			res.render('home', {
				title : 'Control Panel',
				countries : CT,
				udata : req.session.user
			});
	    }
	});

	app.get('/investigator/profile', function(req, res) {
	    if (req.session.user == null){
	// if user is not logged-in redirect back to login page //
	        res.redirect('/');
	    }   else{
			res.render('home', {
				title : 'Control Panel',
				countries : CT,
				udata : req.session.user
			});
	    }
	});


	app.post('/profile', function(req, res){
		if (req.param('user') != undefined) {
			console.log(req.param('anz-identity'));
			AM.updateAccount({
				user 		: req.param('email'),
				name 		: req.param('name'),
				email 		: req.param('email'),
				bio 		: req.param('bio'),
				experimentInfo 		: req.param('experimentInfo'),
				country 	: req.param('country'),
				pass		: req.param('pass'),
				anz		: req.param('anz'),
				anzName		: req.param('anz-name'),
				anzIdentity		: req.param('anz-identity')
			}, function(e, o){
				if (e){
					res.send('error-updating-account', 400);
				}	else{
					req.session.user = o;
			    // update the user's login cookies if they exists //
					if (req.cookies.user != undefined && req.cookies.pass != undefined){
						res.cookie('user', o.user, { maxAge: 900000 });
						res.cookie('pass', o.pass, { maxAge: 900000 });	
					}
					res.send('ok', 200);
				}
			});
		}	else if (req.param('logout') == 'true'){
			res.clearCookie('user');
			res.clearCookie('pass');
			req.session.destroy(function(e){ res.send('ok', 200); });
		}
	});
	
		app.post('/investigator/profile', function(req, res){
		if (req.param('user') != undefined) {
			console.log(req.param('anz-identity'));
			AM.updateAccount({
				user 		: req.param('email'),
				name 		: req.param('name'),
				email 		: req.param('email'),
				bio 		: req.param('bio'),
				experimentInfo 		: req.param('experimentInfo'),
				country 	: req.param('country'),
				pass		: req.param('pass'),
				anz		: req.param('anz'),
				anzName		: req.param('anz-name'),
				anzIdentity		: req.param('anz-identity')
			}, function(e, o){
				if (e){
					res.send('error-updating-account', 400);
				}	else{
					req.session.user = o;
			    // update the user's login cookies if they exists //
					if (req.cookies.user != undefined && req.cookies.pass != undefined){
						res.cookie('user', o.user, { maxAge: 900000 });
						res.cookie('pass', o.pass, { maxAge: 900000 });	
					}
					res.send('ok', 200);
				}
			});
		}	else if (req.param('logout') == 'true'){
			res.clearCookie('user');
			res.clearCookie('pass');
			req.session.destroy(function(e){ res.send('ok', 200); });
		}
	});
	




// creating new accounts //
	
	app.get('/signup', function(req, res) {
		res.render('signup', {  title: 'Signup', countries : CT });
	});
	
	app.post('/signup', function(req, res){
		AM.addNewAccount({
			name 	: req.param('name'),
			email 	: req.param('email'),
			bio 	: req.param('bio'),
			experimentInfo 	: req.param('experimentInfo'),
			user 	: req.param('email'),
			pass	: req.param('pass'),
			country : req.param('country')
		}, function(e){
			if (e){
				res.send(e, 400);
			}	else{
				res.send('ok', 200);
			}
		});
	});

// password reset //

	app.post('/lost-password', function(req, res){
	// look up the user's account via their email //
		AM.getAccountByEmail(req.param('email'), function(o){
			if (o){
				res.send('ok', 200);
				EM.dispatchResetPasswordLink(o, function(e, m){
				// this callback takes a moment to return //
				// should add an ajax loader to give user feedback //
					if (!e) {
					//	res.send('ok', 200);
					}	else{
						res.send('email-server-error', 400);
						for (k in e) console.log('error : ', k, e[k]);
					}
				});
			}	else{
				res.send('email-not-found', 400);
			}
		});
	});

	app.get('/reset-password', function(req, res) {
		var email = req.query["e"];
		var passH = req.query["p"];
		AM.validateResetLink(email, passH, function(e){
			if (e != 'ok'){
				res.redirect('/');
			} else{
	// save the user's email in a session instead of sending to the client //
				req.session.reset = { email:email, passHash:passH };
				res.render('reset', { title : 'Reset Password' });
			}
		})
	});
	
	app.post('/reset-password', function(req, res) {
		var nPass = req.param('pass');
	// retrieve the user's email from the session to lookup their account and reset password //
		var email = req.session.reset.email;
	// destory the session immediately after retrieving the stored email //
		req.session.destroy();
		AM.updatePassword(email, nPass, function(e, o){
			if (o){
				res.send('ok', 200);
			}	else{
				res.send('unable to update password', 400);
			}
		})
	});
	
// view & delete accounts //
	
	app.get('/print', function(req, res) {
		AM.getAllRecords( function(e, accounts){
			res.render('print', { title : 'Account List', accts : accounts });
		})
	});
	
	app.post('/delete', function(req, res){
		AM.deleteAccount(req.body.id, function(e, obj){
			if (!e){
				res.clearCookie('user');
				res.clearCookie('pass');
	            req.session.destroy(function(e){ res.send('ok', 200); });
			}	else{
				res.send('record not found', 400);
			}
	    });
	});
	
	app.get('/reset', function(req, res) {
		AM.delAllRecords(function(){
			res.redirect('/print');	
		});
	});

// investigator path
	app.get('/investigator', function(req, res) {
    res.render('investigator', {  title: 'Signup', countries : CT });
	});

	app.get('/front_page', function(req, res) {
		if (req.session.user == null){
	  // if user is not logged-in redirect back to login page //
	        res.redirect('/');
	    }   else{
	    console.log("at front page!")
	    console.log (req.session.user);
			res.render('front_page', {  
				title: 'Investigator Front Page', 
				countries : CT , 
				user : req.session.user
			});
		}
	});

	app.get('/investigator/front_page', function(req, res) {
		if (req.session.user == null){
	  // if user is not logged-in redirect back to login page //
	        res.redirect('/');
	    }   else{
	    console.log("at front page!")
	    console.log (req.session.user);
			res.render('front_page', {  
				title: 'Investigator Front Page', 
				countries : CT , 
				user : req.session.user
			});
		}
	});

	app.get('/dataview', function(req, res) {
		console.log("dataview requst");
		console.log(req.param('s'));
		SU.getScientist(req.param('s'), function(o){
			if (o != null) ){
				console.log('found the scientist!');
				console.log(o);
			  // something lke anz_log: 'FDDS2015-20130416-233912Z-DataLog_User_Minimal.dat'
				// 'FDDS2015-20130416-233912Z-DataLog_User_Minimal.dat'.match(/\w{0,9}/)
				// ["FDDS2015"]
				if (o.anz_log) {
					var anz_log_name = o.anz_log.match(/\w{0,9}/)[0];	
				} else{
					res.send('no analyzer found for this experiment', 400);
				};

			  AM.getAccountByAnzLog(anz_log_name,function(o2){
					if (o2){
						console.log('has account from anz_log!');
						res.render('public_url', {
				      // user : AM.get.user()
				      pageData : {
				    						 scientistName: o2.name,
				    	           project: o2.experimentInfo,
                         bio: o2.bio
                       },
				      title: 'Investigator',
				      countries : CT
				    });
				  } else{
					  res.send('no scientist found for this analyzer', 400);				  
					}
				});	
			}	else {
				res.send('dataview not found for this short code', 400);
			}
		});
	});


app.get('/investigator/dataview', function(req, res) {
		console.log("dataview requst");
		console.log(req.param('s'));
		SU.getScientist(req.param('s'), function(o){
			if (o != null) ){
				console.log('found the scientist!');
				console.log(o);
			  // something lke anz_log: 'FDDS2015-20130416-233912Z-DataLog_User_Minimal.dat'
				// 'FDDS2015-20130416-233912Z-DataLog_User_Minimal.dat'.match(/\w{0,9}/)
				// ["FDDS2015"]
				if (o.anz_log) {
					var anz_log_name = o.anz_log.match(/\w{0,9}/)[0];	
				} else{
					res.send('no analyzer found for this experiment', 400);
				};

			  AM.getAccountByAnzLog(anz_log_name,function(o2){
					if (o2){
						console.log('has account from anz_log!');
						res.render('public_url', {
				      // user : AM.get.user()
				      pageData : {
				    						 scientistName: o2.name,
				    	           project: o2.experimentInfo,
                         bio: o2.bio
                       },
				      title: 'Investigator',
				      countries : CT
				    });
				  } else{
					  res.send('no scientist found for this analyzer', 400);				  
					}
				});	
			}	else {
				res.send('dataview not found for this short code', 400);
			}
		});
	});

// @app.route('/investigator')
// def investigator():
//     amplitude = float(request.values.get('amplitude',0.1))
//     do_not_follow = int('do_not_follow' in request.values)
//     follow = int('follow' in request.values or not do_not_follow)
//     center_longitude = float(request.values.get('center_longitude',-121.98432))
//     center_latitude = float(request.values.get('center_latitude',37.39604))
//     return render_template('investigator_ben.html',amplitude=amplitude,follow=follow,do_not_follow=do_not_follow,
//                                        center_latitude=center_latitude,center_longitude=center_longitude)
	
	app.get('*', function(req, res) { res.render('404', { title: 'Page Not Found'}); });




};