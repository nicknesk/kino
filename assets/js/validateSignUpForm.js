function isLetter(symbol) {
    var regex = /^([a-zA-Z])/;
    return regex.test(symbol);
}

function isLogin(login) {
    var regex = /^([a-zA-Z0-9_.])+$/;
    return regex.test(login);
};

function isEmail(email) {
  var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
  return regex.test(email);
};

function validateSignUpInput () {
    var errorMessage = "";
    var login = $("#login").val();
    var email = $("#email").val();
    var password = $("#password").val();
    var password_confirm =$("#password_confirm").val();

    if (isLetter(login[0]) == false) {
        errorMessage += "<br>Login must begin with letter";
    }
    if (isLogin(login) == false) {
        errorMessage += "<br>Invalid login";
    }
    if (isEmail(email) == false) {
        errorMessage += "<br>Invalid e-mail";
    }
    if (password != password_confirm) {
        errorMessage += "<br>Passwords does not match";
    }
    return errorMessage;
};

$('#sign_up_btn').click(function(event) {
     var errorMessage = validateSignUpInput();
     $("#inputError").hide();
     $("#userExistsError").hide();
     if (errorMessage != "") {
         event.preventDefault();
       /*  $('#sign_up_btn').attr('onclick','').unbind('click'); */
         $("#inputError").fadeIn();
         $("#errorMessage").html(errorMessage);
     } else {
         $("#successMessage").show();
     }
 });