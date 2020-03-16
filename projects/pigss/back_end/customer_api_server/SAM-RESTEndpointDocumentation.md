# SAM: REST Endpoint

The document outlines endpoints that can be used to get measurements from the SAM system.

<ip_address>: IP address of the SAM system (e.g. 127.0.0.1 is the IP address of localhost).
* **Getting IP of SAM System**:
    * Press `Super` Key (Windows Keys) and start typing `Network`
    * Click on `Network` in `Settings`
    * Click the gear icon of Ethernet (en01)
    * Note down `IPv4 Address`

## Get Available Keys

#### URL

`http://<ip_address>:8000/public/api/v0.1/getkeys`

#### Method`

`GET`

#### URL Params

None

#### Data Params

None

#### Success Response

* **Code**: 200
* **Content**: `{ "keys": ["CH4", "CO2", "CavityPressure", "CavityTemp"] }`

#### Error Response

**Bad Resquest**: Incorrect use of API, most likely error in passed `URL`
* **Code**: 400 Bad Request
* **Content**: `Please check for inorrect use of API. The API requested, could not be found.`

#### Sample Call

`curl -X GET --header 'Accept: application/json' 'http://<ip_address>:8000/public/api/v0.1/getkeys'`

<hr />

## Get Points

#### URL

`http://<ip_address>:8000/public/api/v0.1/getpoints`

#### Method

`GET`

#### URL Params

##### Required

* **keys**: available field keys for measurement, can be fetched using `Get Available Keys` endpoint

##### Optional

* **from**: sets start time for fetching records,
    * UTC format or epoch
* **to**: sets end time for fetching records
    * UTC format or epoch
* **epoch**: `true` if epoch time is passed

Note: If none of the fields specified above are passed in, the most recent data is returned.

#### Data Params

None

#### Success Response

* **Code**: 200
* **Content**: `{"points": [{"time": 1583946245223, "CavityPressure": 140, "valve_pos": "0"}]}`

#### Error Response

**Bad Resquest**: Incorrect use of API, most likely error in passed `URL`
* **Code**: 400 Bad Request
* **Content**: `Please check for inorrect use of API. The API requested, could not be found.`

**Internal Server Error**: Incorrect use of API, most likely error in passed `URL Params`
* **Code**: 500 Internal Server Error
* **Content**: `Server got itself in trouble.`

#### Sample Call

`curl -X GET --header 'Accept: application/json' 'http://<ip_address>:8000/public/api/v0.1/getpoints?keys=NH3&from=1571141669042&to=1571332469042&epoch=true'`

`curl -X GET --header 'Accept: application/json' 'http://<ip_address>:8000/public/api/v0.1/getpoints?keys=NH3&keys=H2O&from=2019-10-15T12:14:29.042Z&to=2019-10-17T17:14:29.042Z'`

<hr/>
