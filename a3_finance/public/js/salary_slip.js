frappe.ui.form.on('Salary Slip',{
    refresh(frm){
        frm.fields_dict.deductions.grid.wrapper.find('[data-fieldname="custom_actual_amount').hide();

        frm.fields_dict.deductions.on('grid-row-render',function(row){
            row.grid_form.fields_dict.custom_actual_amount.df.hidden = 1;
            row.grid_form.fields_dict.custom_actual_amount.refresh();
        })
        // Target only the deductions grid table
        const deductions_wrapper = frm.fields_dict.deductions.grid.wrapper;

        // Hide the column header for 'Actual Amount' in deductions
        deductions_wrapper.find('th[data-fieldname="custom_actual_amount"]').hide();

        // Hide the column cells for all rows
        deductions_wrapper.find('td[data-fieldname="custom_actual_amount"]').hide();

        // Keep it hidden even after row refresh or add
        frm.fields_dict.deductions.grid.on('grid-row-render', function(row) {
            const $row = $(row.row);
            $row.find('td[data-fieldname="custom_actual_amount"]').hide();
        });
        // Function to hide the last column ("Actual Amount") in deductions
        function hide_actual_amount_in_deductions() {
            const wrap = frm.fields_dict['deductions'].grid.wrapper;

            // Hide the static column headers
            wrap.find('.grid-heading-row .col:contains("Actual Amount")').hide();

            // Hide the column content in each row
            wrap.find('.grid-body .grid-row').each(function () {
                $(this).find('.col').filter(function () {
                    return $(this).text().trim() === "Actual Amount" || 
                           $(this).closest('.grid-static-col').index() === 3;
                }).hide();
            });
        }

        // Initial hide after refresh
        setTimeout(hide_actual_amount_in_deductions, 300);

        // Re-apply hide whenever grid rows change
        frm.fields_dict['deductions'].grid.on('grid-row-render', () => {
            hide_actual_amount_in_deductions();
        });
        // Use jQuery to hide the section by its class or ID
        $(document).ready(function() {
            // Replace with the actual class or ID of the section
            $('.col grid-static-col col-xs-2  text-right').hide();

            // Optional: Add a debug message
            console.log("hidden.");
        });
    
    
},
onload(frm){
    frm.set_df_property('total_working_days', 'hidden', 1);
    frm.set_df_property('payment_days', 'hidden', 1);
    frm.set_df_property('custom_gross_actual_amount','read_only', 1);
    frm.set_df_property('custom_gross_deduction_year_to_date','read_only', 1);
}
});

