# proxy-api

REST API for web reverse proxy by standalone envoy.

`Client -- HTTP port + path --> Proxy -- HTTP port + path + HTTP Host header --> Backends`

## Setup
Depending on following tools:
- Python 3.8
- dockert and docker-compose

```bash
make build_api
make build_woker
docker-compose up
```

## REST API

### Endpoint

#### Add endpoint

request:

```bash
curl -X POST http://localhost:8888/v1/endpoints \
-H "Accept: application/json" \
-d '{"port_value": "8888", "route": "/", "host_header": "www.google.com"}'
```

result:

```text
HTTP/1.1 202 Accepted
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 04:53:50 GMT
Content-Length: 38

{"message": "Operation was accepted."}
```

#### List endpoints

request:

```bash
curl -X GET http://localhost:8888/v1/endpoints
```

result:

```text
HTTP/1.1 200 OK
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 08:34:06 GMT
Etag: "0439d81ad97eb69d0b458d2decc1b6727bccc232"
Content-Length: 278

{
  "endpoints": [
    {
      "address": "0.0.0.0",
      "port_value": "18080",
      "filters": [
        {
          "domains": [
            "*"
          ],
          "routes": [
            {
              "endpoint_uuid": "abd9aef89a54956244894f9360ff9ba0",
              "prefix": "/",
              "request_headers_to_add": [
                {
                  "header": {
                    "key": "Host",
                    "value": "www.google.com"
                  },
                  "append": false
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### Get endpoints

request:

```bash
curl -X GET http://localhost:8888/v1/endpoints/<endpoint_uuid>
```

result:

```text
HTTP/1.1 200 OK
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 08:31:36 GMT
Etag: "0439d81ad97eb69d0b458d2decc1b6727bccc232"
Content-Length: 278

{
  "endpoints": [
    {
      "address": "0.0.0.0",
      "port_value": "18080",
      "filters": [
        {
          "domains": [
            "*"
          ],
          "routes": [
            {
              "endpoint_uuid": "abd9aef89a54956244894f9360ff9ba0",
              "prefix": "/",
              "request_headers_to_add": [
                {
                  "header": {
                    "key": "Host",
                    "value": "www.google.com"
                  },
                  "append": false
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### Delete endpoint

request:

```bash
curl -X DELETE http://localhost:8888/v1/endpoints/<endpoint_uuid>
```

result:

```text
HTTP/1.1 202 Accepted
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 10:21:19 GMT
Content-Length: 38

{"message": "Operation was accepted."}
```

### Backend servers

#### Add server

request:

```bash
curl -X POST http://localhost:8888/v1/endpoints/<endpoint_uuid>/servers \
-H "Accept: application/json" \
-d '{"address": "172.217.175.110", "port": 8080}'
```

result:

```text
HTTP/1.1 202 Accepted
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 09:48:36 GMT
Content-Length: 38

{"message": "Operation was accepted."}
```

#### List servers

request:

```bash
curl -X GET http://localhost:8888/v1/endpoints/<endpoint_uuid>/servers
```

result:

```text
HTTP/1.1 200 OK
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 10:17:42 GMT
Etag: "cf7d70f67953c8b8803343c54bbc62630bf5fc71"
Content-Length: 591

{
  "endpoints": [
    {
      "address": "0.0.0.0",
      "port_value": "18080",
      "filters": [
        {
          "domains": [
            "*"
          ],
          "routes": [
            {
              "endpoint_uuid": "abd9aef89a54956244894f9360ff9ba0",
              "prefix": "/",
              "request_headers_to_add": [
                {
                  "header": {
                    "key": "Host",
                    "value": "www.google.com"
                  },
                  "append": false
                }
              ],
              "lb_policy": "ROUND_ROBIN",
              "endpoints": [
                {
                  "server_uuid": "e2da01b3c77761b857a9f24283f7469d",
                  "address": {
                    "socket_address": {
                      "address": "172.217.175.110",
                      "port_value": 80
                    }
                  }
                },
                {
                  "server_uuid": "7f75f01c15d0905383df408b506d33af",
                  "address": {
                    "socket_address": {
                      "address": "172.217.175.110",
                      "port_value": 8080
                    }
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### Delete server

request:

```bash
curl -X DELETE http://localhost:8888/v1/endpoints/<endpoint_uuid>/servers/<server_uuid>
```

result:

```text
HTTP/1.1 202 Accepted
Server: TornadoServer/6.1
Content-Type: application/json
Date: Fri, 25 Dec 2020 10:46:42 GMT
Content-Length: 38

{"message": "Operation was accepted."}
```
