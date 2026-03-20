# -*- coding: utf-8 -*-
from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _auto_merge_find_target_id(self, company_id, product_id):
        """
        Βρίσκει την παλαιότερη MO (create_date ASC) για ίδιο product και εταιρεία,
        σε κατάσταση draft ή confirmed, και την κλειδώνει (FOR UPDATE) για
        αποφυγή race conditions.
        """
        self.env.cr.execute(
            """
            SELECT id
            FROM mrp_production
            WHERE company_id = %s
            AND product_id = %s
            AND state IN ('draft', 'confirmed')
            ORDER BY create_date ASC, id ASC
            LIMIT 1
            FOR UPDATE
            """,
            (company_id, product_id),
        )
        row = self.env.cr.fetchone()
        return row[0] if row else False

    def _auto_merge_add_qty(self, target_mo, vals):
        """
        Προσθέτει την ποσότητα από τα vals στην υπάρχουσα MO, με μετατροπή μονάδας
        αν χρειάζεται. Ενημερώνει και τα stock moves ώστε το forecasted qty
        να είναι σωστό στο product page.
        """
        add_qty = float(vals.get("product_qty") or 0.0)
        if not add_qty:
            return

        vals_uom_id = vals.get("product_uom_id")
        if vals_uom_id and vals_uom_id != target_mo.product_uom_id.id:
            from_uom = self.env["uom.uom"].browse(vals_uom_id)
            add_qty = from_uom._compute_quantity(
                add_qty,
                target_mo.product_uom_id,
                round=False,
            )

        new_qty = target_mo.product_qty + add_qty

        # Ενημερώνουμε την ποσότητα της MO
        target_mo.write({"product_qty": new_qty})

        # ✅ Ενημερώνουμε το finished product move (αυτό που τροφοδοτεί το forecast)
        finished_moves = target_mo.move_finished_ids.filtered(
            lambda m: m.product_id == target_mo.product_id
                      and m.state not in ('done', 'cancel')
        )
        if finished_moves:
            finished_moves.write({"product_uom_qty": new_qty})

        # ✅ Invalidate cache για να ανανεωθεί το forecasted qty παντού
        target_mo.invalidate_recordset()
        finished_moves.invalidate_recordset()
        target_mo.product_id.invalidate_recordset()

        # Προαιρετικά: συγχώνευση origin
        new_origin = (vals.get("origin") or "").strip()
        if new_origin:
            existing_origin = (target_mo.origin or "").strip()
            if not existing_origin:
                target_mo.write({"origin": new_origin})
            elif new_origin not in existing_origin.split(", "):
                target_mo.write(
                    {"origin": f"{existing_origin}, {new_origin}"}
                )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Αν υπάρχει ήδη MO για ίδιο product (draft/confirmed),
        κάνει merge στην παλαιότερη και δεν δημιουργεί νέα.
        """
        # Δυνατότητα να απενεργοποιήσεις τη συμπεριφορά με context.
        if self.env.context.get("disable_auto_merge_mo"):
            return super().create(vals_list)

        created_or_merged = self.browse()
        to_create = []

        # Cache ανά (company, product) για το ίδιο create_multi.
        cache_target_by_key = {}

        for vals in vals_list:
            product_id = vals.get("product_id")
            qty = vals.get("product_qty")
            if not product_id or not qty:
                to_create.append(vals)
                continue

            company_id = vals.get("company_id") or self.env.company.id
            key = (company_id, product_id)

            target = cache_target_by_key.get(key)
            if not target:
                target_id = self._auto_merge_find_target_id(
                    company_id, product_id
                )
                target = self.browse(target_id) if target_id else self.browse()
                cache_target_by_key[key] = target

            if target:
                self._auto_merge_add_qty(target, vals)
                created_or_merged |= target
            else:
                to_create.append(vals)

        if to_create:
            created = super().create(to_create)
            for mo in created:
                cache_target_by_key[(mo.company_id.id, mo.product_id.id)] = mo
            created_or_merged |= created

        return created_or_merged
