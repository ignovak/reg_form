$('#login_btn').click(function() {
  $('#greetings').hide();
  $('#login_form').show();
  return false
});

$('#logout_btn').click(function() {
  $.get('/logout', function() {
      
    $('#head').html("<span class='label'>Hi, guest</span>   \
      <a id='login_btn' href='login'>Login</a>    \
      <a href='/register'>Register</a>");
    $('#greetings').show();
    $('#login_form').hide();
  })
  return false
});

$('#login_form form').submit(function() {
  $.post('/login', $(this).serialize(), function(data) {
    if (data.error) {
      if (!$('#login_form .error')[0])
        $('#login_form form').prepend($('<li class="error"></li>'));

      $('#login_form .error').text(data.error);
    } else {
      $('#head').html("<span class='label'>You are logged in as " + data.name + "</span> \
                    <a id='logout_btn' href='logout'>Logout</a>");
      $('#greetings').show();
      $('#login_form').hide();
    }
  }, 'json')
  return false 
});
