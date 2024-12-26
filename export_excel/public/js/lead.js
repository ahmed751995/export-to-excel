frappe.ui.form.on("Lead", {
  refresh(frm) {
    // your code here
    frm.add_custom_button(
      __("Export to Excel"),
      function () {
        frappe.call({
          method: "export_excel.api.get_lead_as_excel",
          type: "GET",
          args: { name: frm.doc.name },
          callback: function (r) {
            if (r.message.success) {
              window.open(r.message.file_url, '_blank').focus();
            }
          },
        });
      },
      __("Action"),
    );
  },
});
