# payments test app

## Android

`android.test.*` purchases should always work, won't always be signed though.

More info: [http://developer.android.com/guide/market/billing/billing_testing.html](http://developer.android.com/guide/market/billing/billing_testing.html)

To sign use `android.key` with password `"password"` and key `"key"` with password
`"password"`. 

Upload to your Google Play account @ [https://play.google.com/apps/publish/](https://play.google.com/apps/publish/) and
create a test account to use in the apps. 

Test account purchases WILL be charged (so cancel them after).

## iOS

Create a `io.trigger.test.payments` provisioning profile and a test user from iTunes
Connect or nothing will work.