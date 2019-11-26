## Tfy

Tiffany Customizations

#### License

MIT

### Functionality

Item Price History

- The *Item Price History* doctype stores the history of prices that are submitted via Purchase Receipt. The data in this doctype is exposed via whitelisted method.

Pincode Distance

- The distance between two pin codes is stored in the *Pincode Distance* doctype. This is used to default the distance on the Sales Invoice.

Accounting Dimension Default

- The doctype *Accounting Dimension Default* stores default values of the configurable accounting dimensions by *Transaction Type*. The *Transaction Type* is selected on the Sales Invoice and it defaults the dimensions on the Sales Invoice appropriately.

Tax gross up accounting

- Based on the income and expense account set up in the *Custom Settings* doctype an additional accounting entry is created on a Sales Invoice with GST. This entry books the GST amount into the appropriate GST Income and GST Expense accounts set up in the *Custom Settings* doctype.

Store Code

- The *Store Code* doctype stores a mapping between the company, merchant and terminal ID. This is used later on in reconciliation of the Bank File Data.

Bank File Data

- The *Bank File Data* doctype stores the data uploaded via a Bank File. This file contains fields like Bank ID, Terminal ID, Credit Card No, Authorization Code and Amount. These fields are matched with the Sales Invoice and appropriate reconciliation accounting entry is created based on the Account setup in the *Bank* doctype. 

