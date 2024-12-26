import frappe
from frappe import _
import xlsxwriter
from io import BytesIO
import os
from PIL import Image

target_width = 100
target_height = 70


def get_absolute_files_path():
    bench_root = frappe.utils.get_bench_path()

    site_path = frappe.get_site_path()[2:]
    absolute_site_path = os.path.join(bench_root, "sites", site_path)

    return absolute_site_path


def calculate_scaling_factors(image_path, target_width, target_height):
    # Open the image and get its original size
    with Image.open(image_path) as img:
        original_width, original_height = img.size

    # Calculate scale factors based on target pixel dimensions
    x_scale = target_width / original_width
    y_scale = target_height / original_height

    return x_scale, y_scale


@frappe.whitelist(allow_guest=True)
def get_lead_as_excel(name):
    absolute_path = get_absolute_files_path()
    Lead = frappe.qb.DocType("Lead")
    BillOfQuantity = frappe.qb.DocType("Bill of Quantity")

    data = (
        frappe.qb.from_(Lead)
        .left_join(BillOfQuantity)
        .on(Lead.name == BillOfQuantity.parent)
        .select(Lead.star, BillOfQuantity.star)
        .where(Lead.name == name)
        .run(as_dict=True)
    )

    if not data:
        return

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    bold_format = workbook.add_format({"bold": True, "font_size": 14})

    data = [data[0]] + data

    for row_num, row_data in enumerate(data):
        if row_num == 0:
            columns = row_data.keys()
        else:
            columns = row_data.values()
            worksheet.set_row(row_num, 60)
        for col_num, cell_data in enumerate(columns):
            if row_num == 0:
                worksheet.write(row_num, col_num, cell_data, bold_format)
            else:
                if list(row_data.keys())[col_num] == "attach_image_wjpb":
                    if "/private/" not in cell_data:
                        image_path = absolute_path + "/public/"
                    else:
                        image_path = absolute_path

                    image_path += cell_data
                    x_scale, y_scale = calculate_scaling_factors(
                        image_path, target_width, target_height
                    )
                    worksheet.insert_image(
                        row_num,
                        col_num,
                        image_path,
                        {"x_scale": x_scale, "y_scale": y_scale},
                    )
                else:
                    worksheet.write(row_num, col_num, cell_data)

    worksheet.set_column("A:XFD", 15)
    workbook.close()

    file_exists = frappe.db.exists(
        "File",
        {
            "file_name": "exported_excel.xlsx",
            "attached_to_doctype": "Lead",
            "attached_to_name": name
        },
    )

    print(file_exists)
    if file_exists:
        frappe.delete_doc("File", file_exists)

    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": "exported_excel.xlsx",  
            "is_private": 1,  
            "content": output.getvalue(),
            "attached_to_doctype": "Lead",
            "attached_to_name": name
        }
    )

    file_doc.save()
    frappe.db.commit()
    return {"success": True, "file_url": file_doc.file_url}
