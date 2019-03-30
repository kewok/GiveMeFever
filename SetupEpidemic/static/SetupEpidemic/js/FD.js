/* java script for displaying forms in modals. Based on: https://github.com/sibtc/simple-ajax-crud */

$(function () {
  /* Functions */
  var loadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-FD .modal-content").html("");
        $("#modal-FD").modal("show");
      },
      success: function (data) {
        $("#modal-FD .modal-content").html(data.html_form);
      }
    });
  };

  var saveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#modal-FD").modal("hide");
	  window.location.replace("/SetupEpidemic/submit_transmission?transmission_mode=FD" + data.hosts_encountered);
        }
        else {
          $("#modal-FD .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };


  /* Binding */

  // Create FD
  $(".js-create-FD").click(loadForm);
  $("#modal-FD").on("submit", ".js-create-FD-form", saveForm);
});
