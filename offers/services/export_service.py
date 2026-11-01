import csv

from django.http import HttpResponse
from django.utils.text import slugify


def is_value_empty(val):
    if val is None or val == "":
        return True
    if isinstance(val, str) and val.strip().lower() in ("", "none", "null"):
        return True
    return False


def export_customers_to_csv(
    queryset, filename_prefix="customers", date_label="all", prune_empty=True
):
    """
    Exports a queryset of Customer models to a CSV HttpResponse.
    """
    safe_name = slugify(filename_prefix) if filename_prefix else "customers"
    date_str = date_label or "all"
    filename = f"{safe_name}_{date_str}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    columns_def = [
        ("Date of Purchase", lambda c, g: c.date_of_purchase),
        ("Customer Name", lambda c, g: c.customer_name),
        ("Shop Name", lambda c, g: c.shop_name),
        ("Sold Area", lambda c, g: c.sold_area),
        ("Region", lambda c, g: c.region or ""),
        ("Phone Number", lambda c, g: c.phone_number),
        ("Email", lambda c, g: c.email or ""),
        ("Phone Model", lambda c, g: c.phone_model or ""),
        ("Sale Status", lambda c, g: c.sale_status or ""),
        ("Prize Details", lambda c, g: c.prize_details or ""),
        ("IMEI", lambda c, g: c.imei or ""),
        ("Gift", lambda c, g: ", ".join([gift.name for gift in g]) if g else ""),
        ("How Know About Campaign", lambda c, g: c.how_know_about_campaign or ""),
        ("Profession", lambda c, g: c.profession or ""),
    ]

    all_rows = []
    for customer in queryset:
        gifts = list(customer.gift.all())
        row = [getter(customer, gifts) for _, getter in columns_def]
        all_rows.append(row)

    if prune_empty and all_rows:
        active_indices = [
            col_idx
            for col_idx in range(len(columns_def))
            if any(not is_value_empty(row[col_idx]) for row in all_rows)
        ]
    else:
        active_indices = list(range(len(columns_def)))

    headers = [columns_def[idx][0] for idx in active_indices]
    writer.writerow(headers)

    for row in all_rows:
        filtered_row = [row[idx] for idx in active_indices]
        writer.writerow(filtered_row)

    return response
