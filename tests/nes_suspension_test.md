# NES Suspsension Test #
In order to verify NES suspesnion is working, run the following steps.

## Setup
1. Make sure that the 'nes_on_flag' ConfigMap has the product type you are testing set to 'True'

### Set up GD Test account and WM Product
Skip these steps if you already have a GoDaddy test account and a WM test product
1. Create a GoDaddy test account
    1. Go to https://www.test-godaddy.com/
    1. Click 'Sign In' > 'Create Account'
    1. Enter personal information for test account
1. Create a Websites + Marketing product in your test account
    1. Click on your name in the upper right, and select 'My Products'
    1. Under Websites + Marketing, create a WM product and follow the prompts.  This will create a website for you with a free trial period.
    1. Go back to the products page, click on "Update payment method" under the new website you generated in the 'Websites + Marketing' section
    1. Select a payment method and plan.
    1. Enter a payment.  The credit card number must be a valid format and the date needs to be in the future.  I use 4111-1111-1111-1111 for a card number since visa's need to start with 4.
1. Update your website's domain
    1. On the Products page, click on the website you just created
    1. Click 'Use my domain' next to the website URL on this page.  Either select a domain you already own, or create a new one.
1. Publish your website
    1. On the Products page, click on the website you just created
    1. On the upper right hand corner, click 'Publish'

## Create a ticket
1. Go to Phishenet test environment
1. Open the "Ticket Creation" tab
1. Put your WM domain into the 'Source(s)' textbox.  Fill in other required data on the form
1. Submit the Ticket
1. Copy that ticket ID for later use
1. Open MongoDB test
1. Search for that ticket number
1. Wait for the 'phishstory_status' on that ticket to go from 'PROCESSING' to 'OPEN'

## Perform a suspension on that ticket
1. In phishnet, open up the "Tickets" tab
1. Find the ticket you just created, and click on the lock next to that ticket
1. Open the 'Select Ticket Action' dropdown, and select 'Suspend'
1. Back in Mongo, wait for that ticket to go to 'CLOSED'

## Verification
1. Verify your product no longer exists in your test account.
    1. Log into your account on the godaddy test page
    1. Click on your name, and open the 'Products" menu
    1. Verify the WM product you suspended is no longer in that list
1. Verify the entitlement status is now SUSPENDED
    1. Using postman, or CURL, create a GET requests with the following parameters.  Note that 'customerID' is your test account customerID, and 'entitlementId' is the GUID associated with that the hosting account:
        1. url = https://entitlements-ext.cp.api.test.godaddy.com/v2/customers/{customerID}/entitlements/{entitlementId}
        1. Headers: 
            1. Authorization = sso-jwt {jwt for zeus client cert}
            1. x-app-key = zeus
    1. Verify the response you get back, has a 'status' of SUSPENDED 
