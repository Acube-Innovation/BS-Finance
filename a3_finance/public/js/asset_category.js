frappe.ui.form.on('Asset Category', {
    onload: function(frm) {
        frm.set_query('custom_parent_asset_category', () => {
            return {
                filters: {
                    custom_is_group: 1
                }
            };
        });
    }
});


// frappe.treeview_settings["Asset Category"] = {
//     breadcrumb: "Assets",
//     title: __("Asset Category"),
//     get_tree_nodes: function (parent) {
//         return frappe.call({
//             method: "a3_finance.doc_events.api.get_asset_category_tree",
//             args: { parent: parent },
//             callback: function (r) {
//                 if (r.message) {
//                     frappe.treeview_settings["Asset Category"].render_nodes(r.message);
//                 }
//             }
//         });
//     },
//     onload: function (tree) {
//         // Optional: Action when tree loads
//     },
//     onrender: function (node) {
//         // Optional: Add custom actions per node
//     }
// };
frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Asset Category"] = {
    breadcrumb: "Assets",
    title: __("Asset Category Hierarchy"),
    get_tree_root: false,

    root_label: "Asset Categories",
    get_tree_nodes: "your_app.your_module.get_asset_category_children",

    fields: [
        {
            fieldtype: "Data",
            fieldname: "asset_category_name",
            label: __("Category Name"),
            reqd: true
        },
        {
            fieldtype: "Check",
            fieldname: "custom_is_group",
            label: __("Is Group"),
            description: __("Groups can have child categories; non-groups are leaf nodes.")
        },
        {
            fieldtype: "Link",
            fieldname: "custom_parent_asset_category",
            label: __("Parent Category"),
            options: "Asset Category",
            description: __("Leave blank for root level categories.")
        },
        {
            fieldtype: "Small Text",
            fieldname: "custom_description",
            label: __("Description")
        }
    ],

    ignore_fields: ["custom_parent_asset_category"],

    onload: function (treeview) {
        frappe.treeview_settings["Asset Category"].treeview = {};
        $.extend(frappe.treeview_settings["Asset Category"].treeview, treeview);
    },

    post_render: function (treeview) {
        frappe.treeview_settings["Asset Category"].treeview["tree"] = treeview.tree;
        if (treeview.can_create) {
            treeview.page.set_primary_action(
                __("New"),
                function () {
                    const node = treeview.tree.get_selected_node();
                    if (node.is_root) {
                        frappe.throw(__("Cannot create root Asset Category."));
                    }
                    treeview.new_node();
                },
                "add"
            );
        }

        // Auto-expand first root for user friendliness
        let firstRootNode = treeview.tree.wrapper.find('.tree-node:first');
        if (firstRootNode.length) {
            treeview.tree.toggle_node(firstRootNode);
        }
    },

    toolbar: [
        {
            label: __("Add Child"),
            condition: function (node) {
                return (
                    frappe.boot.user.can_create.indexOf("Asset Category") !== -1 &&
                    node.expandable &&
                    !node.is_root
                );
            },
            click: function () {
                var me = frappe.views.trees["Asset Category"];
                me.new_node();
            }
        }
    ],
    extend_toolbar: true
};