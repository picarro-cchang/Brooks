# Customer Facing API

## API Endpoints

### Get Available Keys

    /api/v0.1/getkeys

### Get Points

    /api/v0.1/getpoints

#### URL Parameters

* keys: available field keys from measurement
* from: sets start time for fetching records,
    * UTC format or epoch
    * *optional*
* to: sets end time for fetching records
    * UTC format or epoch
    * optional
* epoch: `true` if epoch time is passed

Examples

`/api/v0.1/getpoints?keys=NH3&from=1571141669042&to=1571332469042&epoch=true`

`/api/v0.1/getpoints?keys=NH3&keys=H2O&from=2019-10-15T12:14:29.042Z&to=2019-10-17T17:14:29.042Z`