# MRP Auto Merge by Product

Odoo 17 module that automatically merges draft Manufacturing Orders
(MOs) for the same product into a single MO, keeping the MRP
planning cleaner and easier to manage.

---

## Overview

In many manufacturing workflows, multiple draft MOs are created for
the same product (for example from different Sales Orders or manual
entries). This can quickly clutter the MRP dashboard and make it
harder to plan production.

This module automatically detects compatible draft Manufacturing
Orders for the same product and merges them into a single MO by
summing their quantities.

---

## Features

- Automatically merges draft Manufacturing Orders for the same
  product.
- Merges only MOs that are compatible (same product, BoM and basic
  parameters).
- Resulting MO has a quantity equal to the sum of the merged MOs.
- Cancels or archives the original draft MOs after merging.
- Keeps manufacturing flows cleaner, with fewer and larger MOs.

> Note: Adjust this section if your implementation uses different
> rules or additional filters for merging.

---

## How it works

- The module extends the `mrp.production` model and introduces logic
  to search for draft MOs that can be merged.
- When a new draft MO is created (or on a manual action, depending
  on your implementation), the module:
  - looks for other draft MOs with the same product (and optionally
    same BoM, routing, company, etc.),
  - computes the total quantity,
  - writes this quantity on a single "master" MO,
  - and cancels/marks as merged the redundant MOs.

---

## Installation

1. Download or clone this repository.
2. Copy the module folder (for example `mrp_auto_merge_by_product`)
   into your Odoo `custom_addons` directory.
3. Restart the Odoo server.
4. Activate **Developer Mode** in Odoo.
5. Go to **Apps** → click **Update Apps List**.
6. Search for **MRP Auto Merge by Product** and install the module.

---

## Usage

1. Configure your usual Manufacturing setup:
   - Products with BoMs.
   - MOs created from Sales Orders or manually.
2. Create several draft Manufacturing Orders for the same product.
3. Depending on the implementation:
   - Either the merge is triggered automatically on MO creation,
   - Or you have a server action / button to run the merge
     on selected draft MOs.
4. After the merge:
   - Check that there is a single MO with the combined quantity.
   - The original draft MOs should be cancelled or flagged as merged.

> Adapt the steps above according to how your module triggers the
> merge (on create, cron, server action, button, etc.).

---

## Configuration

The default behaviour is designed to be safe and conservative.
Typical options that can be customized in the code:

- Which fields must match for MOs to be considered "mergeable"
  (product, BoM, company, planned date, etc.).
- Whether to merge only draft MOs or also confirmed ones.
- What happens to the original MOs after merging
  (cancel, archive, mark as merged).

---

## Compatibility

- Odoo 17 Community
- Odoo 17 Enterprise

Other Odoo versions are not officially supported and may require
code adjustments.

---

## Development & contributions

Issues, suggestions and pull requests are welcome.

When opening an issue, please include:

- Odoo edition and version.
- Exact module version (if you use tags, e.g. `v17.0.1.0.0`).
- Clear steps to reproduce the problem.
- Any relevant logs or stack traces.

---

## License

This module is licensed under the **LGPL-3.0**
(GNU Lesser General Public License v3.0).

See the `LICENSE` file in the root of the repository for the full
license text.
