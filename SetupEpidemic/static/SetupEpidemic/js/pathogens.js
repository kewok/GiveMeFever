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
        $("#modal-neoforma .modal-content").html("");
        $("#modal-neoforma").modal("show");
      },
      success: function (data) {
        $("#modal-neoforma .modal-content").html(data.html_form);
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
          $("#modal-neoforma").modal("hide");
	  window.location.replace("/SetupEpidemic/CompartmentSelection?species=PN");
        }
        else {
          $("#modal-neoforma .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };


  /* Binding */

  // Create pathogen
  $(".js-create-pathogen").click(loadForm);
  $("#modal-neoforma").on("submit", ".js-pathogen-create-form", saveForm);
});
