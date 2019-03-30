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
        $("#modal-SIR .modal-content").html("");
        $("#modal-SIR").modal("show");
      },
      success: function (data) {
        $("#modal-SIR .modal-content").html(data.html_form);
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
          $("#modal-SIR").modal("hide");
	  window.location.replace("/SetupEpidemic/TransmissionSelection?epidemic_key="+data.epidemic_key);
        }
        else {
          $("#modal-SIR .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };


  /* Binding */

  // Create SIR
  $(".js-create-SIR").click(loadForm);
  $("#modal-SIR").on("submit", ".js-create-SIR-form", saveForm);

});
