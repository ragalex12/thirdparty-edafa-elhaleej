# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def action_update_cost_from_bom_and_labor(self):
        """
        Calculates the cost of a BoM by:
        1. Exploding it and summing the costs of raw components (materials)
        2. Querying past completed MOs to get average labor cost per unit
        3. Combining both to update the product's standard_price
        
        This method can be called from a button on the mrp.bom form.
        """
        # Use a single environment for all calculations to improve performance.
        # active_test=False allows finding archived products if they are in the BoM.
        self_env = self.with_context(active_test=False)
        
        for bom in self_env:
            _logger.info("Starting cost calculation (materials + labor) for BoM: %s (%s)", 
                        bom.display_name, bom.id)

            # --- 1. Determine the final product to update ---
            if bom.product_id:
                product_to_update = bom.product_id
            elif bom.product_tmpl_id and len(bom.product_tmpl_id.product_variant_ids) == 1:
                # If the BoM is for a template with only one variant, update that variant.
                product_to_update = bom.product_tmpl_id.product_variant_id
            else:
                _logger.warning(
                    "BoM %s (%s) has no specific product variant to update. Skipping.",
                    bom.display_name, bom.id
                )
                continue

            # --- 2. Explode the BoM to get all raw components (MATERIAL COST) ---
            try:
                # explode() returns (boms_done, lines_done)
                # lines_done is a list of (bom_line, line_data) for raw materials
                boms_done, lines_done = bom.explode(product_to_update, bom.product_qty)
            except UserError as e:
                # This can happen if a component is not stockable and has no BoM itself.
                raise UserError(
                    _("Error exploding BoM '%s': %s") % (bom.display_name, e)
                )

            total_material_cost = 0.0
            component_details_log = []

            if not lines_done:
                _logger.warning("BoM %s (%s) has no component lines after explosion.", 
                               bom.display_name, bom.id)
                # If there are no components, material cost is 0

            # --- 3. Sum the cost of all raw components (MATERIALS) ---
            for line, line_data in lines_done:
                component = line.product_id
                component_cost = component.standard_price
                quantity = line_data['qty']
                
                if component_cost <= 0:
                    _logger.warning(
                        "Component '%s' in BoM '%s' has a cost of 0 or less. "
                        "This may lead to an inaccurate total cost.",
                        component.display_name, bom.display_name
                    )

                line_total = component_cost * quantity
                total_material_cost += line_total
                component_details_log.append(
                    f"  - {component.display_name}: {quantity} x {component_cost} = {line_total}"
                )

            # --- 4. Query past completed MOs for average LABOR cost ---
            company = bom.company_id or self.env.company
            # Search for completed MOs; filter for those with timesheet labor in Python
            # (timesheet_labor_cost is computed, can't be used in search domain)
            all_completed_mos = self.env['mrp.production'].search([
                ('product_id', '=', product_to_update.id),
                ('state', '=', 'done'),
                ('company_id', '=', company.id),
            ])
            # Filter: only MOs with timesheet_ids and positive labor cost
            past_mos = all_completed_mos.filtered(
                lambda mo: mo.timesheet_ids and mo.timesheet_labor_cost > 0
            )

            avg_labor_per_unit = 0.0
            labor_details_log = ""
            
            if past_mos:
                total_labor = sum(mo.timesheet_labor_cost for mo in past_mos)
                total_qty = sum(mo.product_qty for mo in past_mos)
                
                if total_qty > 0:
                    avg_labor_per_unit = total_labor / total_qty
                    labor_details_log = (
                        f"  - Average labor from {len(past_mos)} completed MOs\n"
                        f"  - Total labor: {total_labor:.2f} for {total_qty:.2f} units\n"
                        f"  - Average per unit: {avg_labor_per_unit:.4f}"
                    )
                    _logger.info("Found %d past MOs for product '%s'. Avg labor per unit: %.4f",
                                len(past_mos), product_to_update.display_name, avg_labor_per_unit)
                else:
                    _logger.warning("Past MOs found but total quantity is 0. Labor cost will be 0.")
                    labor_details_log = "  - No valid quantity from past MOs (labor = 0)"
            else:
                _logger.warning(
                    "No completed MOs with timesheet labor found for product '%s'. "
                    "Labor cost will be 0. Cost will include materials only.",
                    product_to_update.display_name
                )
                labor_details_log = "  - No completed MOs with timesheet labor found (labor = 0)"

            # --- 5. Compute total cost (material + labor) and normalize per unit ---
            if bom.product_qty <= 0:
                _logger.error(
                    "BoM %s (%s) has a product quantity of 0, cannot calculate unit cost. Skipping.",
                    bom.display_name, bom.id
                )
                continue

            # Material cost is already total for bom.product_qty
            # Labor cost needs to be scaled by bom.product_qty
            total_labor_cost = avg_labor_per_unit * bom.product_qty
            total_cost = total_material_cost + total_labor_cost
            final_cost_per_unit = total_cost / bom.product_qty

            # Store old cost for comparison
            old_cost = product_to_update.standard_price

            # --- 6. Update the product's cost (standard_price) ---
            _logger.info(
                "Updating cost for product '%s' from BoM '%s'.\n"
                "Old Cost: %.4f\n"
                "--- Material Cost Breakdown ---\n%s\n"
                "Total Material: %.4f\n"
                "--- Labor Cost Breakdown ---\n%s\n"
                "Total Labor: %.4f\n"
                "--- Final Cost ---\n"
                "Total Cost: %.4f for %.2f units\n"
                "New Cost per Unit: %.4f",
                product_to_update.display_name,
                bom.display_name,
                old_cost,
                "\n".join(component_details_log) if component_details_log else "  (no components)",
                total_material_cost,
                labor_details_log,
                total_labor_cost,
                total_cost,
                bom.product_qty,
                final_cost_per_unit
            )
            
            product_to_update.standard_price = final_cost_per_unit
            
            # --- 7. Post a message on the product's chatter for traceability ---
            material_summary = (
                f"<strong>{len(component_details_log)} components</strong>" 
                if component_details_log else "<em>No components</em>"
            )
            labor_summary = (
                f"<strong>{len(past_mos)} past MOs</strong>" 
                if past_mos else "<em>No past MOs</em>"
            )
            
            message = _(
                "Product cost updated from Bill of Materials <strong>%(bom_name)s</strong>:<br/>"
                "<ul>"
                "<li>Material cost: <strong>%(material_cost).2f</strong> (from %(material_summary)s)</li>"
                "<li>Labor cost: <strong>%(labor_per_unit).4f</strong>/unit (avg from %(labor_summary)s)</li>"
                "<li>Total: <strong>%(total_cost).2f</strong> for %(bom_qty).2f units</li>"
                "</ul>"
                "Cost per unit: <strong>%(old_cost).2f</strong> → <strong>%(new_cost).4f</strong>",
                bom_name=bom.display_name,
                material_cost=total_material_cost,
                material_summary=material_summary,
                labor_per_unit=avg_labor_per_unit,
                labor_summary=labor_summary,
                total_cost=total_cost,
                bom_qty=bom.product_qty,
                old_cost=old_cost,
                new_cost=final_cost_per_unit
            )
            product_to_update.message_post(body=message)

        # --- 8. Return user notification ---
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cost Updated'),
                'message': _('Product cost has been updated with materials and labor.'),
                'type': 'success',
                'sticky': False,
            }
        }
