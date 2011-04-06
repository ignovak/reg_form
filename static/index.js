$('#login_btn').click(function() {
  console.log('login')
  $('#greetings').hide();
  $('#login_form').show();
  return false
});

$('#logout_btn').click(function() {
  console.log('logout')
  $.get('/logout', function() {
    console.log('logout ok')
    $('#head').html("Hi, guest    \
      <a id='login_btn' href='login'>Login</a>    \
      <a href='/register'>Register</a>");
    $('#greetings').show();
    $('#login_form').hide();
  })
  return false
});

$('#login_form form').submit(function() {
  $.post('/login', $(this).serialize(), function(data) {
      console.log(data)
    if (data.error) {
      console.log('error')
      if (!$('.login_form .error')[0])
        $('.login_form form').prepend($('<li class="error"></li>'));

      $('.login_form .error').text(data.error);
    } else {
      $('#head').html("Hi, " + data.name +
        "<a id='logout_btn' href='logout'>Logout</a>");
      $('#greetings').show();
      $('#login_form').hide();
    }
  }, 'json')
  return false 
});
