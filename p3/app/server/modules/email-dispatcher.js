
var ES = require('./email-settings');
var EM = {};
module.exports = EM;

EM.server = require("emailjs/email").server.connect({

	host 	    : ES.host,
	user 	    : ES.user,
	password    : ES.password,
	ssl		    : true

});

EM.dispatchResetPasswordLink = function(account, callback)
{
	EM.server.send({
		from         : ES.sender,
		to           : account.email,
		subject      : 'Password Reset',
		text         : 'something went wrong... :(',
		attachment   : EM.composeEmail(account)
	}, callback );
}

EM.composeEmail = function(o)
{
	var link = 'http://node-login.braitsch.io/reset-password?e='+o.email+'&p='+o.pass;
	var html = "<html><body>";
		html += "Hi "+o.name+",<br><br>";
		html += "Your username is :: <b>"+o.user+"</b><br><br>";
		html += "<a href='"+link+"'>Please click here to reset your password</a><br><br>";
		html += "Cheers,<br>";
		html += "<a href='http://twitter.com/braitsch'>braitsch</a><br><br>";
		html += "</body></html>";
	return  [{data:html, alternative:true}];
}

EM.dispatchScientistEmail = function(to,name,email,comment, callback)
{
	EM.server.send({
		from         : email,
		to           : to,
		subject      : 'Message from a viewer of your dataview',
		text         : comment,
		attachment   : EM.emailScientist(name,email,comment)
	}, callback );
}

EM.emailScientist = function(name,email,comment)
{
	var html = "<html><body>";
	  html += "The following message came from someone identifying themselves as " + name; //+ "while viewing the dataview " + dataview;
    html += "<br /><p>"
		html += comment
		html += "</p></body></html>";
	return  [{data:html, alternative:true}];
}