$(':submit').click(function() {
  var error = foundErrors();
  if (error) {
    if (!$('.error')[0])
      $('ol').prepend($('<li class="error"></li>'));

    $('.error').text(ERROR_MESSAGES[error]);
    return false
  } 
  function foundErrors() {
    if ($('input').filter(function(){return $(this).val() == ''})[0])
      return 'emptyField'

    if ($('input').filter(function(){return $(this).val().length > 100})[0])
      return 'tooLongValue'

    if (!/^[-.\w]+@(?:[a-z\d][-a-z\d]+\.)+[a-z]{2,6}$/.test($('#email').val()))
      return 'incorrectEmail'

    if (!/^\w+$/.test($('#password').val()))
      return 'wrongPassword'

    if ($('#password').val() != $('#confirmPassword').val())
      return 'wrongConfirmation'

    if (!/^\w+$/.test($('#name').val()))
      return 'wrongName'
  };
})
