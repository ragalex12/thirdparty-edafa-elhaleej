/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { markup } from "@odoo/owl";
import { ProjectRightSidePanel } from "@project/components/project_right_side_panel/project_right_side_panel";

patch(ProjectRightSidePanel.prototype, {
    get panelVisible() {
        return super.panelVisible || this.state.data.show_project_details;
    },

    get descriptionMarkup() {
        const description = this.state.data.description;
        if (!description) {
            return markup("");
        }
        return markup(description);
    },

    get hasDescription() {
        return Boolean(this.state.data.description);
    },

    get hasContractAmount() {
        return Boolean(
            this.state.data.show_contract_amount && this.state.data.contract_amount
        );
    },
});
