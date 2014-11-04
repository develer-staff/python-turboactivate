# Change Log

All notable changes to this project are documented in this file.

## 1.0.3 - 2014-11-04

### Changed

* `TurboActivate.activate()` throws an exception if activation fails

## 1.0.2 - 2014-11-03

### Changed

* Calling `SetCustomActDataPath` under Linux will raise a runtime exception since the method is not
  available on that platform.


## 1.0.1 - 2014-09-29

### Added

* `TurboActivate.is_date_valid()` now accepts an optional `date` parameter, which must be a
  string.


### Fixed

* We use the correct buffer allocation scheme when using `GetFeatureValue`.'
* Solved a packaging problem (README.rst was not included in the distribution).


## 1.0.0 - 2014-08-12

First public version
