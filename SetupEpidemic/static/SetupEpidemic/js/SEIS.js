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
        $("#modal-SEIS .modal-content").html("");
        $("#modal-SEIS").modal("show");
      },
      success: function (data) {
        $("#modal-SEIS .modal-content").html(data.html_form);
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
          $("#modal-SEIS").modal("hide");
	  window.location.replace("/SetupEpidemic/TransmissionSelection?epidemic_key="+data.epidemic_key);
        }
        else {
          $("#modal-SEIS .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };


  /* Binding */

  // Create SEIS
  $(".js-create-SEIS").click(loadForm);
  $("#modal-SEIS").on("submit", ".js-create-SEIS-form", saveForm);
});
