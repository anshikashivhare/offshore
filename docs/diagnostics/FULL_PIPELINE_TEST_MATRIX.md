# Full Pipeline Test Matrix

| Test Case | Description | Planner Execution | Route / Valid Status | Target Integration Objective |
|---|---|---|---|---|
| **TEST 1** | Port Origins | NOT IMPLEMENTED | N/A | Missing robust integration from Frontend API. |
| **TEST 2** | Coordinate Origin -> Dest | PASSED | GeoJSON Returned / Validated | Valid coordinates resolve perfectly. |
| **TEST 3** | Safety Objective | PARTIAL | GeoJSON Returned | Heuristics partially executed. |
| **TEST 4** | Fuel Objective | NOT IMPLEMENTED | N/A | Hardcoded to shortest or astar. |
| **TEST 5** | Time Objective | PARTIAL | GeoJSON Returned | Time ETA exists but dynamic forecasting lacks hook. |
| **TEST 6** | Land Obstruction | PASSED | 40-node route woven / Validated | Planner navigates constraints beautifully. |
| **TEST 7** | Invalid Endpoint | PASSED | API Error 400 | Deep inland routes properly rejected safely. |
| **TEST 8** | Missing Iceberg Data | BLOCKED | Icebergs Default 0 | API pipeline skips candidate injection. |
| **TEST 9** | Missing Sea Ice Data | BLOCKED | Sea Ice 0 | API pipeline ignores full resolution. |
| **TEST 10** | Horizon Exceeded | NOT IMPLEMENTED | N/A | Unhandled in API logic. |
| **TEST 11** | Antimeridian Case | PASSED | N/A | Underlying validation module processes it natively. |
| **TEST 12** | Database Unavailable | PASSED | Connection Refused / 500 | Standard SQLAlchemy failures. |
