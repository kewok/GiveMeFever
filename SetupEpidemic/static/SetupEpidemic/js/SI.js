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
        $("#modal-SI .modal-content").html("");
        $("#modal-SI").modal("show");
      },
      success: function (data) {
        $("#modal-SI .modal-content").html(data.html_form);
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
          $("#modal-SI").modal("hide");
	  window.location.replace("/SetupEpidemic/TransmissionSelection?epidemic_key="+data.epidemic_key);
        }
        else {
          $("#modal-SI .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };


  /* Binding */

  // Create SI
  $(".js-create-SI").click(loadForm);
  $("#modal-SI").on("submit", ".js-create-SI-form", saveForm);
});
